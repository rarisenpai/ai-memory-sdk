from re import I
from typing import List, Dict, Any
from src.database import Message, File


messages_prompt = "The following message interactions have occured"
messages_tag = "messages"
message_total_char_limit = 5000 # how many character are included in a message chunk accross all messages

file_tag = "file"
file_part_tag = "file_part"
file_char_limit = 5000 # how many character to include in file part 

def format_messages(messages: List[Message]) -> List[str]:
    """
    Format messages like the following: 

    user: hi my name is sarah
    assistant: Hello Sarah! I'm Sam. smiles warmly There's something special about first meetings, don't you think? Like opening a book to its first page, full of possibilities. I'd love to get to know you better - what brings you here today?
    assistant: Tool call returned Sent message successfully.

    """
    message_history = "\n".join([
        f"{msg.role}: {msg.content}" for msg in messages
    ])

    return [{"role": "user", "content": f"<{messages_tag}>{messages_prompt}:\n{message_history}</{messages_tag}>"}]

def format_files(files: List[File]) -> List[str]:
    """
    Format files like the following to send in parts: 

    <file_part n/{total_count}><label>label</label><description>description</description><content>content</content></file>
    """

    # chunk up files into parts 
    file_parts = []
    for file in files:
        file_content = file.content
        file_content_chunks = [file_content[i:i + file_char_limit] for i in range(0, len(file_content), file_char_limit)]
        for i, chunk in enumerate(file_content_chunks):
            file_parts.append({
                "n": i + 1,
                "total_count": len(file_content_chunks),
                "label": file.label,
                "description": file.description,
                "content": chunk
            })

    def format_part(part):
        return f"<{file_part_tag} part={part['n']}/{len(file_parts)}>{part['content']}</{file_part_tag}>"

    # TODO: break this up into more than one time message if the total content is too large
    file_prompt_start = f"<{file_tag} label={file.label} description={file.description}>"
    file_prompt_end = f"</{file_tag}>"
    file_prompt = file_prompt_start + "\n".join(format_part(part) for part in file_parts) + file_prompt_end

    print(file_prompt)

    return [{"role": "user", "content": file_prompt}]
    

    