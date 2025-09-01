import { LettaClient } from '@letta-ai/letta-client';
import { SubconsciousDatabase } from './database.js';
import { formatMessages, formatFiles } from './promptFormatter.js';
import type { 
  MessageCreate, 
  DatabaseStats, 
  LettaMessage, 
  LettaRun, 
  LettaBlock, 
  LettaAgent 
} from './types.js';

export class Run {
  private runId: string;
  private lettaClient: LettaClient;

  constructor(runId: string, lettaClient: LettaClient) {
    this.runId = runId;
    this.lettaClient = lettaClient;
  }

  async getStatus(): Promise<string> {
    const run = await this.lettaClient.runs.retrieve(this.runId);
    return run.status;
  }
}

export class SubconsciousAgent {
  public agentId: string;
  private lettaClient: LettaClient;
  private db: SubconsciousDatabase;

  constructor(agentId: string, lettaClient: LettaClient, dbPath: string = "subconscious.db") {
    this.agentId = agentId;
    this.lettaClient = lettaClient;
    this.db = new SubconsciousDatabase(dbPath);
  }

  async learn(revise: boolean = false): Promise<Run> {
    if (revise) {
      this.db.resetProcessingStatus(this.agentId);
    }

    // Get unprocessed items
    const unprocessedMessages = this.db.getUnprocessedMessages(this.agentId);
    const unprocessedFiles = this.db.getUnprocessedFiles(this.agentId);

    // Aggregate messages to send
    const messagesToSend: LettaMessage[] = [];

    // Process messages
    if (unprocessedMessages.length > 0) {
      this.db.markMessagesProcessed(unprocessedMessages.map(msg => msg.id));
      messagesToSend.push(...formatMessages(unprocessedMessages));
    }

    // Process files
    if (unprocessedFiles.length > 0) {
      this.db.markFilesProcessed(unprocessedFiles.map(file => file.id));
      messagesToSend.push(...formatFiles(unprocessedFiles));
    }

    // Create a run to track the learning process
    if (messagesToSend.length > 0) {
      let index = 0;
      let lastRun: LettaRun | null = null;

      for (const messages of messagesToSend) {
        console.log("SENDING MESSAGES", JSON.stringify(messages).length);
        
        // Start async operation (returns immediately with run ID)
        let run = await this.lettaClient.agents.messages.createAsync(this.agentId, {
          messages: [messages]
        });

        // Poll for completion
        while (run.status !== "completed") {
          await new Promise(resolve => setTimeout(resolve, 2000));
          run = await this.lettaClient.runs.retrieve(run.id);
          console.log(`Run ${index + 1}/${messagesToSend.length} STATUS`, run.status);
        }
        
        lastRun = run;
        index++;
      }

      return new Run(lastRun!.id, this.lettaClient);
    } else {
      // No messages to process, create a dummy run
      return new Run('no-processing-needed', this.lettaClient);
    }
  }

  async learnMessages(messages: Record<string, any>[], insertIntoArchivalMemory: boolean = false): Promise<Run> {
    this.registerMessages(messages);
    
    // TODO: Fix archival memory API call
    // if (insertIntoArchivalMemory) {
    //   for (const message of messages) {
    //     await this.lettaClient.agents.passages.create({
    //       agentId: this.agentId,
    //       content: message.content
    //     });
    //   }
    // }

    const unprocessedMessages = this.db.getUnprocessedMessages(this.agentId);
    const formattedMessages = formatMessages(unprocessedMessages);
    
    console.log("FORMATTED MESSAGES", formattedMessages);
    
    // Start async operation (returns immediately with run ID)
    let run = await this.lettaClient.agents.messages.createAsync(this.agentId, {
      messages: formattedMessages
    });

    // Poll for completion
    while (run.status !== "completed") {
      await new Promise(resolve => setTimeout(resolve, 2000));
      run = await this.lettaClient.runs.retrieve(run.id);
    }

    return new Run(run.id, this.lettaClient);
  }

  registerMessages(messages: Record<string, any>[]): number {
    // Convert dict messages to MessageCreate objects
    const messageObjects: MessageCreate[] = messages.map(msg => ({
      content: msg.content || '',
      role: msg.role,
      name: msg.name,
      metadata: Object.fromEntries(
        Object.entries(msg).filter(([key]) => !['content', 'role', 'name'].includes(key))
      )
    }));

    return this.db.registerMessages(this.agentId, messageObjects);
  }

  registerFile(filePath: string, label: string, description: string): boolean {
    return this.db.registerFile(this.agentId, filePath, label, description);
  }

  async createLearnedContextBlock(
    label: string, 
    value: string, 
    description: string, 
    charLimit: number = 10000
  ): Promise<LettaBlock> {
    const block = await this.lettaClient.blocks.create({
      label,
      description,
      limit: charLimit,
      value
    });

    // TODO: Find the correct way to attach blocks to agents
    // await this.lettaClient.agents.blocks.attach({
    //   agentId: this.agentId,
    //   blockId: block.id
    // });

    return block;
  }

  async listLearnedContextBlocks(): Promise<LettaBlock[]> {
    // TODO: Find the correct way to list agent blocks
    return await this.lettaClient.blocks.list();
  }

  async deleteLearnedContextBlock(label: string): Promise<boolean> {
    const block = await this.lettaClient.agents.blocks.retrieve(this.agentId, label);
    if (block) {
      await this.lettaClient.blocks.delete(block.id);
      return true;
    }
    return false;
  }

  async getLearnedContextBlock(label: string): Promise<LettaBlock | null> {
    const block = await this.lettaClient.agents.blocks.retrieve(this.agentId, label);
    return block || null;
  }

  getStats(): DatabaseStats {
    return this.db.getStats(this.agentId);
  }
}

export class LearnedContextClient {
  private lettaClient: LettaClient;

  constructor(lettaApiKey: string) {
    this.lettaClient = new LettaClient({ token: lettaApiKey });
  }

  async createSubconsciousAgent(tags: string[], name: string = "subconscious_agent"): Promise<SubconsciousAgent> {
    const agent = await this.lettaClient.agents.create({
      name,
      // model: "openai/gpt-4.1",
      // agentType: "sleeptime_agent",
      // initialMessageSequence: [],
      // tags
    });

    console.log("tools", agent.tools?.map((t: any) => t.name) || []);
    console.log("NAME", agent.name);
    console.log("AGENT:", agent);

    // const updatedAgent = await this.lettaClient.agents.modify({ agentId: agent.id, requestBody: { tags } });
    // console.log("UPDATE TAGS", updatedAgent.tags);

    return new SubconsciousAgent(agent.id, this.lettaClient);
  }

  async listSubconsciousAgents(tags: string[]): Promise<LettaAgent[]> {
    return await this.lettaClient.agents.list({
      name: `subconscious_agent_user_${tags[0]}`
    });
  }
}

export class ConversationalMemoryClient {
  private lettaClient: LettaClient;
  private client: LearnedContextClient;
  private userContextBlockPrompt: string;
  private userContextBlockCharLimit: number;
  private userContextBlockValue: string;
  private summaryBlockPrompt: string;
  private summaryBlockCharLimit: number;

  constructor(
    lettaApiKey: string,
    userContextBlockPrompt: string = "Details about the human user you are speaking to.",
    userContextBlockCharLimit: number = 10000,
    userContextBlockValue: string = "",
    summaryBlockPrompt: string = "A short (1-2 sentences) running summary of the conversation.",
    summaryBlockCharLimit: number = 1000
  ) {
    this.lettaClient = new LettaClient({ token: lettaApiKey });
    this.client = new LearnedContextClient(lettaApiKey);
    this.userContextBlockPrompt = userContextBlockPrompt;
    this.userContextBlockCharLimit = userContextBlockCharLimit;
    this.userContextBlockValue = userContextBlockValue;
    this.summaryBlockPrompt = summaryBlockPrompt;
    this.summaryBlockCharLimit = summaryBlockCharLimit;
  }

  async add(userId: string, messages: Record<string, any>[]): Promise<Run> {
    const agents = await this.client.listSubconsciousAgents([userId]);
    
    if (agents.length > 0) {
      const agent = agents[0];
      console.log("AGENT EXISTS", agent.id);
      const subconsciousAgent = new SubconsciousAgent(agent.id, this.lettaClient);
      return await subconsciousAgent.learnMessages(messages);
    } else {
      console.log("CREATING AGENT");
      const agent = await this.client.createSubconsciousAgent([userId], `subconscious_agent_user_${userId}`);
      
      const humanBlock = await agent.createLearnedContextBlock(
        "human",
        this.userContextBlockValue,
        this.userContextBlockPrompt,
        this.userContextBlockCharLimit
      );
      
      const summaryBlock = await agent.createLearnedContextBlock(
        "summary",
        "",
        this.summaryBlockPrompt,
        this.summaryBlockCharLimit
      );
      console.log("AGENT CREATED", agent.agentId);

      // attach blocks 
      await this.lettaClient.agents.blocks.attach(agent.agentId, humanBlock.id);
      await this.lettaClient.agents.blocks.attach(agent.agentId, summaryBlock.id);

      return await agent.learnMessages(messages, false);
    }
  }

  async getUserMemory(userId: string): Promise<LettaBlock | null> {
    const agents = await this.client.listSubconsciousAgents([userId]);
    
    if (agents.length > 0) {
      const agent = agents[0];
      const subconsciousAgent = new SubconsciousAgent(agent.id, this.lettaClient);
      return await subconsciousAgent.getLearnedContextBlock("human");
    }
    
    return null;
  }

  async deleteUser(userId: string): Promise<void> {
    const agents = await this.client.listSubconsciousAgents([userId]);
    
    if (agents.length > 0) {
      const agent = agents[0];
      await this.lettaClient.agents.delete(agent.id);
      console.log(`Deleted agent ${agent.id} for user ${userId}`);
    }
  }
}