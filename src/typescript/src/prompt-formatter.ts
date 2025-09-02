import * as fs from 'fs';
import { Message, File, MessageCreate } from './schemas';

const MESSAGES_PROMPT = "The following message interactions have occured";
const MESSAGES_TAG = "messages";
const MESSAGE_TOTAL_CHAR_LIMIT = 5000;

const FILE_TAG = "file";
const FILE_PART_TAG = "file_part";
const FILE_CHAR_LIMIT = 20000;

export function formatMessages(messages: MessageCreate[]): Array<{ role: string; content: string }> {
  const messageHistory = messages
    .map(msg => `${msg.role}: ${msg.content}`)
    .join('\n');

  return [{
    role: "user",
    content: `<${MESSAGES_TAG}>${MESSAGES_PROMPT}:\n${messageHistory}</${MESSAGES_TAG}>`
  }];
}

export function formatFiles(files: File[]): Array<{ role: string; content: string }> {
  const allMessages: Array<{ role: string; content: string }> = [];

  for (const file of files) {
    try {
      const fileContent = fs.readFileSync(file.file_path, 'utf-8');
      
      const fileContentChunks = [];
      for (let i = 0; i < fileContent.length; i += FILE_CHAR_LIMIT) {
        fileContentChunks.push(fileContent.slice(i, i + FILE_CHAR_LIMIT));
      }

      console.log(`Formatted file ${file.label} into ${fileContentChunks.length} separate messages`);

      for (let i = 0; i < fileContentChunks.length; i++) {
        const chunk = fileContentChunks[i];
        const partNumber = i + 1;
        const totalParts = fileContentChunks.length;

        const filePartContent = `<${FILE_PART_TAG} part=${partNumber}/${totalParts}>${chunk}</${FILE_PART_TAG}>`;
        const fileMessage = `<${FILE_TAG} label="${file.label}" description="${file.description}">${filePartContent}</${FILE_TAG}>`;

        allMessages.push({ role: "user", content: fileMessage });
      }
    } catch (error) {
      const errorMsg = `<${FILE_TAG} label="${file.label}" description="${file.description}">[Error reading file: ${error}]</${FILE_TAG}>`;
      allMessages.push({ role: "user", content: errorMsg });
    }
  }

  return allMessages;
}