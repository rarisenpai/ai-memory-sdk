import { LearnedContextClient, ConversationalMemoryClient } from '../src/index';

// Mock environment variable for testing
const LETTA_API_KEY = process.env.LETTA_API_KEY;

describe('Integration Tests', () => {
  beforeEach(() => {
    if (!LETTA_API_KEY) {
      console.warn('LETTA_API_KEY not set, skipping integration tests');
    }
  });

  const testMessages = () => {
    return !LETTA_API_KEY; // Skip if no API key
  };

  describe('Message Registration and Learning', () => {
    it('should register messages and learn from them', async () => {
      if (testMessages()) return;

      const client = new LearnedContextClient(LETTA_API_KEY!);

      // Create the subconscious agent
      const agent = await client.createSubconsciousAgent(['test']);
      console.log('AGENT ID', (agent as any).agentId);

      // Create learned context block
      await agent.createLearnedContextBlock(
        'human',
        '',
        'Information about the human user you are speaking to',
        10000
      );

      // Get the blocks
      const blocks = await agent.listLearnedContextBlocks();
      expect(blocks).toHaveLength(1);
      expect(blocks[0].label).toBe('human');

      // Register messages
      agent.registerMessages([
        {
          role: 'user',
          content: 'Hi my name is Bob'
        },
        {
          role: 'assistant', 
          content: 'Hi Bob, how are you?'
        },
        {
          role: 'user',
          content: "I'm doing well, thank you!"
        }
      ]);

      // Do some learning
      const run = await agent.learn();

      // Wait for completion
      let status = await run.getStatus();
      while (status !== 'completed') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        status = await run.getStatus();
        console.log('STATUS', status);
      }

      console.log('Run completed');

      // Get the block data
      const humanBlock = await agent.getLearnedContextBlock('human');
      expect(humanBlock).toBeTruthy();
      expect(humanBlock!.value).toContain('Bob');
    }, 60000); // 60 second timeout
  });

  describe('Conversational Memory Client', () => {
    it('should handle conversational memory', async () => {
      if (testMessages()) return;

      const client = new ConversationalMemoryClient(LETTA_API_KEY!);
      const testUserId = 'test_user_id_123';

      // Clean up any existing user data
      try {
        await client.deleteUser(testUserId);
      } catch (error) {
        // User might not exist, that's okay
      }

      // Add messages for user
      const run = await client.add(testUserId, [
        {
          role: 'user',
          content: 'Hi my name is Bob'
        }
      ]);

      // Wait for the run to complete
      let status = await run.getStatus();
      while (status !== 'completed') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        status = await run.getStatus();
        console.log('STATUS', status);
      }

      // Get the memory
      const memory = await client.getUserMemory(testUserId);
      expect(memory).toBeTruthy();
      expect(memory!.value).toContain('Bob');
      console.log(memory);

      // Clean up
      await client.deleteUser(testUserId);
    }, 60000); // 60 second timeout
  });
});