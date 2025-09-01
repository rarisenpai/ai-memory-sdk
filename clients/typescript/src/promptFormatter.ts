import { readFileSync } from 'fs';
import type { Message, FileRecord, LettaMessage } from './types.js';

const MESSAGES_PROMPT = "The following message interactions have occured";
const MESSAGES_TAG = "messages";
const MESSAGE_TOTAL_CHAR_LIMIT = 5000;

const FILE_TAG = "file";
const FILE_PART_TAG = "file_part";
const FILE_CHAR_LIMIT = 20000;

export function formatMessages(messages: Message[]): LettaMessage[] {
  const messageHistory = messages
    .map(msg => `${msg.role}: ${msg.content}`)
    .join('\n');

  return [{
    role: "user",
    content: [
      {
        type: "text",
        text: `<${MESSAGES_TAG}>${MESSAGES_PROMPT}:\n${messageHistory}</${MESSAGES_TAG}>`
      }
    ]
  }];
}

export function formatFiles(files: FileRecord[]): LettaMessage[] {
  const allMessages: LettaMessage[] = [];

  for (const file of files) {
    try {
      // Read file content from disk
      const fileContent = readFileSync(file.filePath, 'utf-8');
      
      // Chunk up file content into parts
      const fileContentChunks: string[] = [];
      for (let i = 0; i < fileContent.length; i += FILE_CHAR_LIMIT) {
        fileContentChunks.push(fileContent.slice(i, i + FILE_CHAR_LIMIT));
      }

      console.log(`Formatted file ${file.label} into ${fileContentChunks.length} separate messages`);

      // Create a separate message for each file part
      for (let i = 0; i < fileContentChunks.length; i++) {
        const partNumber = i + 1;
        const totalParts = fileContentChunks.length;
        const chunk = fileContentChunks[i];

        // Create the message content for this specific part
        const filePartContent = `<${FILE_PART_TAG} part=${partNumber}/${totalParts}>${chunk}</${FILE_PART_TAG}>`;
        const fileMessage = `<${FILE_TAG} label="${file.label}" description="${file.description}">${filePartContent}</${FILE_TAG}>`;

        allMessages.push({
          role: "user",
          content: [
            {
              type: "text",
              text: fileMessage
            }
          ]
        });
      }
    } catch (error) {
      // If we can't read the file, send an error message
      const errorMsg = `<${FILE_TAG} label="${file.label}" description="${file.description}">[Error reading file: ${(error as Error).message}]</${FILE_TAG}>`;
      allMessages.push({
        role: "user",
        content: [
          {
            type: "text",
            text: errorMsg
          }
        ]
      });
    }
  }

  return allMessages;
}