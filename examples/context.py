from ai_memory_sdk import Memory


def instance_scoped_example():
    print("== Instance-scoped context example ==")
    memory = Memory(context_id="user_sarah")

    # Create/ensure a block in this context
    memory.initialize_memory(
        label="preferences",
        description="Known user preferences.",
        value="Likes cats",
        reset=True,
    )

    # Add messages to the bound context (unified API)
    run = memory.add_messages([
        {"role": "user", "content": "I love cats"}
    ])
    memory.wait_for_run(run)

    # Read blocks (raw and formatted)
    raw = memory.get_memory("preferences")
    formatted = memory.get_memory("preferences", prompt_formatted=True)
    print("Raw:", raw)
    print("Formatted:", formatted)

    # List and delete
    blocks = memory.list_blocks()
    print("Blocks:", [b.label if hasattr(b, 'label') else b.get('label') for b in blocks])
    memory.delete_block("preferences")
    print("Deleted 'preferences'")


def explicit_context_example():
    print("== Explicit context example ==")
    memory = Memory()

    # Initialize a named context (agent)
    memory.initialize_context("project_alpha", reset=True)

    # Create a block under this context
    memory.initialize_memory(
        label="spec",
        description="Project spec",
        value="v1",
        context_id="project:alpha",
    )

    # Add messages to that context
    run = memory.add_messages_for_context("project_alpha", [
        {"role": "user", "content": "Kickoff complete"}
    ])
    memory.wait_for_run(run)

    spec = memory.get_memory("spec", context_id="project_alpha")
    print("Spec:", spec)


if __name__ == "__main__":
    instance_scoped_example()
    explicit_context_example()
