import { Memory } from '../src/memory';

async function testConversationalMemory() {
  console.log('Testing conversational memory...');
  
  const client = new Memory({ lettaApiKey: process.env.LETTA_API_KEY });
  const testUserId = 'test_user_id_123';

  try {
    // Initialize the user
    await client.initializeUserMemory(testUserId, { reset: true });
    console.log('✓ User memory initialized');

    // Add messages
    const runId = await client.addMessages(testUserId, [
      {
        role: 'user',
        content: 'Hi my name is Bob'
      }
    ]);
    console.log('✓ Messages added');

    // Wait for the run to complete
    await client.waitForRun(runId);
    console.log('✓ Run completed');

    // Get the memory
    const memory = await client.getUserMemory(testUserId);
    if (!memory || !memory.includes('Bob')) {
      throw new Error(`Expected memory to contain 'Bob', got: ${memory}`);
    }
    console.log('✓ Memory contains user name');
    console.log('Memory:', memory);

  } finally {
    // Cleanup
    await client.deleteUser(testUserId);
  }
}

async function testFormattedMemory() {
  console.log('Testing formatted memory...');
  
  const client = new Memory({ lettaApiKey: process.env.LETTA_API_KEY });
  const testUserId = 'test_user_formatted_123';

  try {
    // Initialize user
    await client.initializeUserMemory(testUserId, { reset: true });
    
    const runId = await client.addMessages(testUserId, [
      {
        role: 'user',
        content: 'My favorite color is blue'
      }
    ]);

    await client.waitForRun(runId);

    // Get formatted memory
    const formattedMemory = await client.getUserMemory(testUserId, true);
    if (!formattedMemory || !formattedMemory.includes('<human') || !formattedMemory.includes('blue')) {
      throw new Error(`Expected formatted memory to contain '<human' and 'blue', got: ${formattedMemory}`);
    }
    console.log('✓ Formatted memory is correct');
    console.log('Formatted Memory:', formattedMemory);

  } finally {
    await client.deleteUser(testUserId);
  }
}

async function testMultipleInteractions() {
  console.log('Testing multiple interactions...');
  
  const client = new Memory({ lettaApiKey: process.env.LETTA_API_KEY });
  const testUserId = 'test_user_multi_123';

  try {
    await client.initializeUserMemory(testUserId, { reset: true });

    // First interaction
    let runId = await client.addMessages(testUserId, [
      {
        role: 'user',
        content: 'I work as a software engineer'
      }
    ]);
    await client.waitForRun(runId);

    // Second interaction
    runId = await client.addMessages(testUserId, [
      {
        role: 'user',
        content: 'I enjoy programming in TypeScript'
      }
    ]);
    await client.waitForRun(runId);

    const memory = await client.getUserMemory(testUserId);
    if (!memory) {
      throw new Error('Expected memory to exist after multiple interactions');
    }
    console.log('✓ Multiple interactions handled correctly');
    console.log('Multi-interaction Memory:', memory);

  } finally {
    await client.deleteUser(testUserId);
  }
}

async function testUserDeletion() {
  console.log('Testing user deletion...');
  
  const client = new Memory({ lettaApiKey: process.env.LETTA_API_KEY });
  const testUserId = 'test_user_delete_123';

  // Create user first
  await client.initializeUserMemory(testUserId, { reset: true });
  
  // Verify user exists
  const memoryBefore = await client.getUserMemory(testUserId);
  if (!memoryBefore) {
    throw new Error('Expected user to exist before deletion');
  }
  console.log('✓ User exists before deletion');

  // Delete user
  await client.deleteUser(testUserId);
  console.log('✓ User deleted');

  // Verify user is deleted
  const memoryAfter = await client.getUserMemory(testUserId);
  if (memoryAfter !== null) {
    throw new Error('Expected user to be null after deletion');
  }
  console.log('✓ User memory is null after deletion');
}

async function testNonExistentUser() {
  console.log('Testing non-existent user...');
  
  const client = new Memory({ lettaApiKey: process.env.LETTA_API_KEY });
  const nonExistentUserId = 'non_existent_user_999';
  
  const memory = await client.getUserMemory(nonExistentUserId);
  if (memory !== null) {
    throw new Error('Expected null for non-existent user');
  }
  console.log('✓ Non-existent user returns null');
}

async function testReinitializationError() {
  console.log('Testing reinitialization error...');
  
  const client = new Memory({ lettaApiKey: process.env.LETTA_API_KEY });
  const testUserId = 'test_user_reinit_123';

  try {
    // Create user first
    await client.initializeUserMemory(testUserId, { reset: true });
    console.log('✓ User initialized first time');

    // Try to initialize again without reset
    let errorThrown = false;
    try {
      await client.initializeUserMemory(testUserId, { reset: false });
    } catch (error) {
      if (error.message.includes('already exists')) {
        errorThrown = true;
      } else {
        throw error;
      }
    }

    if (!errorThrown) {
      throw new Error('Expected error when re-initializing without reset');
    }
    console.log('✓ Error thrown for reinitialization without reset');

  } finally {
    await client.deleteUser(testUserId);
  }
}

async function testAddFilesNotImplemented() {
  console.log('Testing addFiles not implemented error...');
  
  const client = new Memory({ lettaApiKey: process.env.LETTA_API_KEY });
  
  let errorThrown = false;
  try {
    await client.addFiles([]);
  } catch (error) {
    if (error.message.includes('Not implemented')) {
      errorThrown = true;
    } else {
      throw error;
    }
  }

  if (!errorThrown) {
    throw new Error('Expected error for unimplemented addFiles');
  }
  console.log('✓ addFiles throws not implemented error');
}

async function runAllTests() {
  console.log('Running Memory tests...\n');

  try {
    await testConversationalMemory();
    console.log();
    
    await testFormattedMemory();
    console.log();
    
    await testMultipleInteractions();
    console.log();
    
    await testUserDeletion();
    console.log();
    
    await testNonExistentUser();
    console.log();
    
    await testReinitializationError();
    console.log();
    
    await testAddFilesNotImplemented();
    console.log();

    console.log('✅ All Memory tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  runAllTests();
}