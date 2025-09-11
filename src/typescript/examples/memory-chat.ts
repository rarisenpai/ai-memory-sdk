import OpenAI from 'openai';
import { createInterface } from 'readline';
import { Memory } from 'ai-memory-sdk';

// Memory is a lightweight client around Letta, and will handle storing information
// about user conversations.
//
// Assumes the existence of the LETTA_API_KEY environment variable, but you can
// set this manually with new Memory({ apiKey: "your_api_key" })
const memory = new Memory();

// Set up your OpenAI client like you normally would.
// This example assumes that the OpenAI key is stored in the OPENAI_API_KEY
// environment variable.
const openaiClient = new OpenAI();

interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

async function chatWithMemories(message: string, userId: string = "default_user"): Promise<string> {
    try {
        // Retrieve the user memory block if it exists, otherwise initialize it
        // User memory blocks are pieces of information about whoever is talking
        // to your assistant, and can be created/retrieved using arbitrary string
        // identifier keys.
        let userMemory = await memory.getUserMemory(userId);
        if (!userMemory) {
            // User doesn't exist, create a new memory block
            await memory.initializeUserMemory(userId, { reset: true });
            userMemory = await memory.getUserMemory(userId);
        }

        // the contents of the user block formatted as a prompt:
        //
        // <human description="Details about the human user you are speaking to.">
        // Name: Sarah
        // Interests: Likes cats (2025-09-04)
        // </human>
        const userMemoryPrompt = await memory.getUserMemory(userId, { promptFormatted: true });
        console.log(userMemoryPrompt);

        // Generate the assistant response using the inference engine of your choice,
        // OpenAI in this case.
        const systemPrompt = `<system>You are a helpful AI assistant</system>\n${userMemoryPrompt}`;

        // Create the list of messages
        const messages: ChatMessage[] = [
            { role: "system", content: systemPrompt },
            { role: "user", content: message }
        ];

        // Send the messages to the OpenAI API
        const response = await openaiClient.chat.completions.create({
            model: "gpt-4o-mini",
            messages: messages
        });

        // Extract the assistant's message from the API response
        const assistantResponse = response.choices[0]?.message?.content || "";

        // Create new memories from the conversation --
        // this will update the user's memory block and persist messages
        console.log("Creating new memories...");
        messages.push({ role: "assistant", content: assistantResponse });
        await memory.addMessages(userId, messages);

        return assistantResponse;
    } catch (error) {
        console.error("Error in chatWithMemories:", error);
        return "Sorry, I encountered an error processing your request.";
    }
}

async function main(): Promise<void> {
    console.log("Chat with AI (type 'exit' to quit)");
    
    const rl = createInterface({
        input: process.stdin,
        output: process.stdout
    });

    const askQuestion = (question: string): Promise<string> => {
        return new Promise((resolve) => {
            rl.question(question, (answer) => {
                resolve(answer);
            });
        });
    };

    try {
        while (true) {
            const userInput = (await askQuestion("You: ")).trim();
            
            if (userInput.toLowerCase() === 'exit') {
                console.log("Goodbye!");
                break;
            }
            
            const response = await chatWithMemories(userInput);
            console.log(`AI: ${response}`);
        }
    } catch (error) {
        console.error("Error in main loop:", error);
    } finally {
        rl.close();
    }
}

// Run the main function if this file is executed directly
if (require.main === module) {
    main().catch((error) => {
        console.error("Fatal error:", error);
        process.exit(1);
    });
}