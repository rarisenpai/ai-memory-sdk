import OpenAI from 'openai';
import { Memory } from '../src/memory';
import * as readline from 'readline';

const openaiClient = new OpenAI();
const memory = new Memory();

async function chatWithMemories(message: string, userId: string = 'default_user'): Promise<string> {
  // Get the user memory
  let userMemory = await memory.getUserMemory(userId);
  if (!userMemory) {
    await memory.initializeUserMemory(userId, { reset: true });
    userMemory = await memory.getUserMemory(userId);
  }

  // Format the user memory
  const userMemoryPrompt = await memory.getUserMemory(userId, true);

  // Generate the assistant response
  let systemPrompt = '<system>You are a helpful AI assistant</system>';
  if (userMemoryPrompt) {
    systemPrompt += `\n${userMemoryPrompt}`;
  }

  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: message }
  ];

  const response = await openaiClient.chat.completions.create({
    model: 'gpt-4o-mini',
    messages
  });

  const assistantResponse = response.choices[0]?.message?.content || 'Sorry, I could not generate a response.';

  // Create new memories from the conversation
  const conversationMessages = [
    { role: 'user', content: message },
    { role: 'assistant', content: assistantResponse }
  ];

  const runId = await memory.addMessages(userId, conversationMessages);
  
  // Note: In a production app, you might want to handle this run completion asynchronously
  // For this example, we'll fire and forget
  memory.waitForRun(runId).catch(console.error);

  return assistantResponse;
}

async function main() {
  console.log('Chat with AI (type \'exit\' to quit)');
  
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const askQuestion = (question: string): Promise<string> => {
    return new Promise((resolve) => {
      rl.question(question, resolve);
    });
  };

  try {
    while (true) {
      const userInput = (await askQuestion('You: ')).trim();
      
      if (userInput.toLowerCase() === 'exit') {
        console.log('Goodbye!');
        break;
      }

      if (userInput) {
        try {
          const aiResponse = await chatWithMemories(userInput);
          console.log(`AI: ${aiResponse}`);
        } catch (error) {
          console.error('Error getting AI response:', error);
          console.log('AI: Sorry, I encountered an error. Please try again.');
        }
      }
    }
  } finally {
    rl.close();
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export { chatWithMemories };