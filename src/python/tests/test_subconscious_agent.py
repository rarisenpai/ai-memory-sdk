import unittest
import tempfile
import os
from unittest.mock import Mock, patch
import sys
import json

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import SubconsciousDatabase, MessageCreate
from src.client import SubconsciousAgent


class TestSubconsciousDatabase(unittest.TestCase):
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = SubconsciousDatabase(self.temp_db.name)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_register_messages(self):
        agent_id = "test_agent_123"
        messages = [
            MessageCreate(content='Hello world', role='user'),
            MessageCreate(content='How are you?', role='user')
        ]
        
        # First registration should add 2 messages
        count = self.db.register_messages(agent_id, messages)
        self.assertEqual(count, 2)
        
        # Second registration of same messages should add 0 (duplicates)
        count = self.db.register_messages(agent_id, messages)
        self.assertEqual(count, 0)
        
        # Check unprocessed messages
        unprocessed = self.db.get_unprocessed_messages(agent_id)
        self.assertEqual(len(unprocessed), 2)
        
        # Verify they are Message objects
        self.assertTrue(all(hasattr(msg, 'id') and hasattr(msg, 'content') for msg in unprocessed))
    
    def test_register_file(self):
        agent_id = "test_agent_123"
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_file_path = f.name
        
        try:
            # First registration should succeed
            result = self.db.register_file(agent_id, temp_file_path, "Test File", "A test file for testing")
            self.assertTrue(result)
            
            # Second registration of same file should fail (already exists)
            result = self.db.register_file(agent_id, temp_file_path, "Test File", "A test file for testing")
            self.assertFalse(result)
            
            # Check unprocessed files
            unprocessed = self.db.get_unprocessed_files(agent_id)
            self.assertEqual(len(unprocessed), 1)
            self.assertEqual(unprocessed[0].file_path, temp_file_path)
            
            # Verify it's a File object
            self.assertTrue(hasattr(unprocessed[0], 'id') and hasattr(unprocessed[0], 'file_path'))
            
        finally:
            os.unlink(temp_file_path)
    
    def test_processing_workflow(self):
        agent_id = "test_agent_123"
        # Register some messages
        messages = [MessageCreate(content='Test message', role='user')]
        self.db.register_messages(agent_id, messages)
        
        # Get unprocessed and mark as processed
        unprocessed = self.db.get_unprocessed_messages(agent_id)
        self.assertEqual(len(unprocessed), 1)
        
        self.db.mark_messages_processed([unprocessed[0].id])
        
        # Should now be no unprocessed messages
        unprocessed = self.db.get_unprocessed_messages(agent_id)
        self.assertEqual(len(unprocessed), 0)
    
    def test_reset_processing_status(self):
        agent_id = "test_agent_123"
        # Register and process a message
        messages = [MessageCreate(content='Test message', role='user')]
        self.db.register_messages(agent_id, messages)
        
        unprocessed = self.db.get_unprocessed_messages(agent_id)
        self.db.mark_messages_processed([unprocessed[0].id])
        
        # Verify it's processed
        self.assertEqual(len(self.db.get_unprocessed_messages(agent_id)), 0)
        
        # Reset processing status
        self.db.reset_processing_status(agent_id)
        
        # Should be unprocessed again
        self.assertEqual(len(self.db.get_unprocessed_messages(agent_id)), 1)
    
    def test_stats(self):
        agent_id = "test_agent_123"
        # Register some messages and files
        messages = [
            MessageCreate(content='Message 1', role='user'),
            MessageCreate(content='Message 2', role='user')
        ]
        self.db.register_messages(agent_id, messages)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_file_path = f.name
        
        try:
            self.db.register_file(agent_id, temp_file_path, "Stats Test File", "File for testing statistics")
            
            stats = self.db.get_stats(agent_id)
            self.assertEqual(stats.total_messages, 2)
            self.assertEqual(stats.unprocessed_messages, 2)
            self.assertEqual(stats.total_files, 1)
            self.assertEqual(stats.unprocessed_files, 1)
            
            # Verify it's a DatabaseStats object
            self.assertTrue(hasattr(stats, 'total_messages') and hasattr(stats, 'processed_messages'))
            
        finally:
            os.unlink(temp_file_path)
    
    def test_multiple_agents_separate_processing(self):
        """Test that different agents have separate processing states"""
        agent1_id = "agent_1"
        agent2_id = "agent_2"
        
        messages = [MessageCreate(content='Shared message', role='user')]
        
        # Register same message for both agents
        count1 = self.db.register_messages(agent1_id, messages)
        count2 = self.db.register_messages(agent2_id, messages)
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)  # Should register separately for each agent
        
        # Both agents should have unprocessed messages
        unprocessed1 = self.db.get_unprocessed_messages(agent1_id)
        unprocessed2 = self.db.get_unprocessed_messages(agent2_id)
        self.assertEqual(len(unprocessed1), 1)
        self.assertEqual(len(unprocessed2), 1)
        
        # Process messages for agent1 only
        self.db.mark_messages_processed([unprocessed1[0].id])
        
        # Agent1 should have no unprocessed, agent2 should still have 1
        unprocessed1 = self.db.get_unprocessed_messages(agent1_id)
        unprocessed2 = self.db.get_unprocessed_messages(agent2_id)
        self.assertEqual(len(unprocessed1), 0)
        self.assertEqual(len(unprocessed2), 1)
        
        # Stats should be separate
        stats1 = self.db.get_stats(agent1_id)
        stats2 = self.db.get_stats(agent2_id)
        self.assertEqual(stats1.processed_messages, 1)
        self.assertEqual(stats2.processed_messages, 0)


class TestSubconsciousAgent(unittest.TestCase):
    
    def setUp(self):
        self.mock_letta_client = Mock()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.agent = SubconsciousAgent(
            agent_id="test_agent_id",
            letta_client=self.mock_letta_client,
            db_path=self.temp_db.name
        )
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_register_messages(self):
        messages = [
            {'content': 'Hello', 'role': 'user'},
            {'content': 'World', 'role': 'assistant'}
        ]
        
        count = self.agent.register_messages(messages)
        self.assertEqual(count, 2)
        
        stats = self.agent.get_stats()
        self.assertEqual(stats.total_messages, 2)
    
    def test_register_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test file content")
            temp_file_path = f.name
        
        try:
            result = self.agent.register_file(temp_file_path, "Agent Test File", "File for testing agent")
            self.assertTrue(result)
            
            stats = self.agent.get_stats()
            self.assertEqual(stats.total_files, 1)
            
        finally:
            os.unlink(temp_file_path)
    
    @patch('src.client.Run')
    def test_learn(self, mock_run_class):
        # Mock the Letta client run creation
        mock_run = Mock()
        mock_run.id = "test_run_id"
        self.mock_letta_client.agents.messages.create_async.return_value = mock_run
        mock_run_instance = Mock()
        mock_run_class.return_value = mock_run_instance
        
        # Register some test data
        messages = [{'content': 'Test message', 'role': 'user'}]
        self.agent.register_messages(messages)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test file")
            temp_file_path = f.name
        
        try:
            self.agent.register_file(temp_file_path, "Learn Test File", "File for testing learn method")
            
            # Call learn
            run = self.agent.learn()
            
            # Verify Letta client was called
            self.mock_letta_client.agents.messages.create_async.assert_called()
            
            # Check that items are marked as processed
            stats = self.agent.get_stats()
            self.assertEqual(stats.unprocessed_messages, 0)
            self.assertEqual(stats.unprocessed_files, 0)
            
        finally:
            os.unlink(temp_file_path)
    
    def test_learn_with_revise(self):
        # Mock the Letta client
        mock_run = Mock()
        mock_run.id = "test_run_id"
        self.mock_letta_client.agents.messages.create_async.return_value = mock_run
        
        # Register and process some data
        messages = [{'content': 'Test message', 'role': 'user'}]
        self.agent.register_messages(messages)
        
        # First learn should process the message
        self.agent.learn()
        stats = self.agent.get_stats()
        self.assertEqual(stats.unprocessed_messages, 0)
        
        # Learn with revise=True should reprocess everything
        self.agent.learn(revise=True)
        
        # Should have called create_async again
        self.assertEqual(self.mock_letta_client.agents.messages.create_async.call_count, 2)


if __name__ == '__main__':
    unittest.main()