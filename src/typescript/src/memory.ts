import { LettaClient } from '@letta-ai/letta-client';
import { formatMessages } from './prompt-formatter';
import { MessageCreate } from './schemas';

export interface MemoryConfig {
  lettaApiKey?: string;
}

export class Memory {
  private lettaClient: LettaClient;

  constructor(config: MemoryConfig = {}) {
    const apiKey = config.lettaApiKey || process.env.LETTA_API_KEY;
    this.lettaClient = new LettaClient({ token: apiKey });
  }

  private async createSleeptimeAgent(name: string, tags: string[]): Promise<string> {
    const agentState = await this.lettaClient.agents.create({
      name,
      model: 'openai/gpt-4',
      agentType: 'sleeptime_agent',
      initialMessageSequence: [],
      tags,
    });
    return agentState.id;
  }

  private async getMatchingAgent(tags: string[]) {
    const agents = await this.lettaClient.agents.list({
      tags,
      matchAllTags: true,
    });
    return agents.length > 0 ? agents[0] : null;
  }

  private async createContextBlock(
    agentId: string,
    label: string,
    description: string,
    charLimit: number = 10000,
    value: string = ''
  ): Promise<string> {
    const block = await this.lettaClient.blocks.create({
      label,
      description,
      limit: charLimit,
      value,
    });
    
    // Attach block to agent
    await this.lettaClient.agents.blocks.attach(agentId, block.id!);
    
    return block.id!;
  }

  private async listContextBlocks(agentId: string) {
    return await this.lettaClient.agents.blocks.list(agentId);
  }

  private async deleteContextBlock(agentId: string, blockId: string): Promise<void> {
    await this.lettaClient.agents.blocks.detach(agentId, blockId);
    await this.lettaClient.blocks.delete(blockId);
  }

  private async deleteAgent(agentId: string): Promise<void> {
    await this.lettaClient.agents.delete(agentId);
  }

  private async learnMessages(agentId: string, messages: Record<string, any>[], skipVectorStorage: boolean = true): Promise<string> {
    const messageCreates = messages.map(msg => ({
      content: msg.content,
      role: msg.role,
      name: msg.name,
      metadata: msg.metadata
    } as MessageCreate));
    const formattedMessages = formatMessages(messageCreates);
    
    console.log('FORMATTED MESSAGES', formattedMessages);
    console.log('AGENT ID', agentId);
    
    const lettaRun = await this.lettaClient.agents.messages.createAsync(agentId, {
      messages: formattedMessages as any,
    });
    
    // Insert into archival in parallel if not skipping vector storage
    if (!skipVectorStorage) {
      const tasks = messages.map(message => 
        this.lettaClient.agents.passages.create(agentId, {
          text: message.content,
          tags: [message.role],
        })
      );
      await Promise.all(tasks);
    }
    
    return lettaRun.id!;
  }

  private formatBlock(block: any): string {
    return `<${block.label} description="${block.description}">${block.value}</${block.label}>`;
  }

  private async getRunStatus(runId: string): Promise<string> {
    const run = await this.lettaClient.runs.retrieve(runId);
    if (!run) {
      throw new Error(`Run ${runId} not found`);
    }
    return run.status!;
  }

  async waitForRun(runId: string): Promise<void> {
    while (await this.getRunStatus(runId) !== 'completed') {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  async initializeUserMemory(
    userId: string,
    options: {
      userContextBlockPrompt?: string;
      userContextBlockCharLimit?: number;
      userContextBlockValue?: string;
      summaryBlockPrompt?: string;
      summaryBlockCharLimit?: number;
      reset?: boolean;
    } = {}
  ): Promise<string> {
    const {
      userContextBlockPrompt = 'Details about the human user you are speaking to.',
      userContextBlockCharLimit = 10000,
      userContextBlockValue = '',
      summaryBlockPrompt = 'A short (1-2 sentences) running summary of the conversation.',
      summaryBlockCharLimit = 1000,
      reset = false,
    } = options;

    // Check if agent already exists
    const existingAgent = await this.getMatchingAgent([userId]);
    if (existingAgent) {
      if (reset) {
        await this.deleteAgent(existingAgent.id);
      } else {
        throw new Error(
          `Agent ${existingAgent.id} already exists for user ${userId}. Cannot re-initialize memory unless deleted.`
        );
      }
    }

    // Create the agent
    const agentId = await this.createSleeptimeAgent(
      `subconscious_agent_user_${userId}`,
      [userId]
    );

    // Create context blocks
    await this.createContextBlock(
      agentId,
      'human',
      userContextBlockPrompt,
      userContextBlockCharLimit,
      userContextBlockValue
    );
    await this.createContextBlock(
      agentId,
      'summary',
      summaryBlockPrompt,
      summaryBlockCharLimit,
      ''
    );

    // Attach a single archival memory (workaround)
    await this.lettaClient.agents.passages.create(agentId, {
      text: `Initialized memory for user ${userId}`,
    });

    return agentId;
  }

  async addMessages(userId: string, messages: Record<string, any>[], skipVectorStorage: boolean = true): Promise<string> {
    let agentId: string;
    const agent = await this.getMatchingAgent([userId]);
    
    if (agent) {
      agentId = agent.id;
    } else {
      agentId = await this.initializeUserMemory(userId);
    }

    return await this.learnMessages(agentId, messages, skipVectorStorage);
  }

  async addFiles(files: Record<string, any>[]): Promise<never> {
    throw new Error('Not implemented');
  }

  async getUserMemory(userId: string, promptFormatted: boolean = false): Promise<string | null> {
    const agent = await this.getMatchingAgent([userId]);
    if (agent) {
      const block = await this.lettaClient.agents.blocks.retrieve(agent.id, 'human');
      if (promptFormatted) {
        return this.formatBlock(block);
      }
      return block.value;
    }
    return null;
  }

  async getSummary(userId: string, promptFormatted: boolean = false): Promise<string | null> {
    const agent = await this.getMatchingAgent([userId]);
    if (agent) {
      const block = await this.lettaClient.agents.blocks.retrieve(agent.id, 'summary');
      if (promptFormatted) {
        return `<conversation_summary>${block.value}</conversation_summary>`;
      }
      return block.value;
    }
    return null;
  }

  async getMemoryAgentId(userId: string): Promise<string | null> {
    const agent = await this.getMatchingAgent([userId]);
    if (agent) {
      return agent.id;
    }
    return null;
  }

  async deleteUser(userId: string): Promise<void> {
    const agent = await this.getMatchingAgent([userId]);
    if (agent) {
      // Deleting the agent also deletes associated messages/blocks
      await this.lettaClient.agents.delete(agent.id);
      console.log(`Deleted agent ${agent.id} for user ${userId}`);
    }
  }

  async search(userId: string, query: string): Promise<string[]> {
    const agent = await this.getMatchingAgent([userId]);
    if (agent) {
      const response = await this.lettaClient.agents.passages.search(agent.id, {
        query,
        tags: ['user'],
      });
      return response.results.map(result => result.content);
    }
    return [];
  }
}