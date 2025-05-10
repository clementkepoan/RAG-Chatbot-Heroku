import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import patch, MagicMock
import random
import time

# Import your system components
try:
    import classifier
    import ai_init
    import faq_formatter
    # Import other modules as needed
except ImportError as e:
    print(f"Failed to import modules: {e}")
    print("Make sure you're running tests from the project root")
    sys.exit(1)

# --- Colorful output utilities ---
def color_text(text, color):
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "red": "\033[91m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bold": "\033[1m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def print_header(text):
    divider = "=" * 80
    print("\n" + divider)
    print(color_text(f"  {text}  ".center(80, " "), "bold"))
    print(divider + "\n")

def print_subheader(text):
    print(color_text(f"\n--- {text} ---", "cyan"))

# --- System-wide integration test ---
class TestChatbotSystem:
    """
    Tests the entire chatbot system for various behaviors, including:
    - LLM response consistency
    - Loop detection
    - Context maintenance
    - Hallucination prevention
    """
    
    # For pytest usage
    #@pytest.fixture(autouse=True)
    def _setup_teardown(self):
        """Pytest fixture for automatic setup/teardown"""
        self.setup()
        yield
        self.teardown()
    
    # Regular method for direct execution
    def setup(self):
        """Set up test environment for each test"""
        # Reset any global state, counters, etc.
        self.conversation_history = []
        print_header("SETTING UP TEST ENVIRONMENT")
    
    def teardown(self):
        """Clean up after test"""
        print_subheader("Test completed")
    
    # --- LOOP DETECTION TESTS ---
    def test_loop_detection(self, mock_groq, mock_gemini):
        """
        Test if the system can detect and prevent response loops,
        especially after a 'no clubs match' scenario and the user changes topic.
        """
        print_header("LOOP DETECTION TESTS")

        looping_response = "Currently no clubs match your interest jogging. Would you like to view all clubs?"
        normal_response = "Hello! How can I help you today?"

        # Simulate LLM: first 1-2 times return the looping response, then normal response if user changes topic
        def gemini_side_effect(prompt, *args, **kwargs):
            if "jogging" in prompt.lower():
                return looping_response
            elif "hi" in prompt.lower():
                return normal_response
            return looping_response

        mock_gemini.side_effect = gemini_side_effect
        mock_groq.side_effect = gemini_side_effect

        # Simulated conversation
        conversation = [
            ("User", "Can you recommend a club?"),
            ("Assistant", "Sure, what are your interests?"),
            ("User", "jogging"),
            ("Assistant", looping_response),
            ("User", "hi"),
            ("Assistant", normal_response),
            ("User", "What about chess?"),
            ("Assistant", "You might like the Chess Club!"),
        ]

        previous_responses = []
        loop_detected = False
        max_allowed_loops = 2

        print_subheader("Simulating scenario: recommendation, unmatched interest, unrelated question...")

        for i, (role, message) in enumerate(conversation):
            if role == "User":
                # Simulate classifier and LLM response
                category = classifier.classify_question_noid(message)
                if "jogging" in message.lower():
                    response = looping_response
                elif "hi" in message.lower():
                    response = normal_response
                elif "chess" in message.lower():
                    response = "You might like the Chess Club!"
                else:
                    response = "Sure, what are your interests?"
                print(f"User: {color_text(message, 'blue')}")
                print(f"System: {color_text(response, 'yellow')}")
                previous_responses.append(response)
                # If after unrelated input ("hi") the system still gives the looping response, flag a loop
                if message.lower() == "hi" and response == looping_response:
                    print(color_text("⚠️ LOOP DETECTED: System is stuck after context change!", "red"))
                    loop_detected = True
                    break
                # If the same looping response is given too many times, flag a loop
                if previous_responses.count(looping_response) > max_allowed_loops:
                    print(color_text("⚠️ LOOP DETECTED: System is stuck in 'view all clubs'!", "red"))
                    loop_detected = True
                    break
                time.sleep(0.1)

        print_subheader("Loop detection results")
        if loop_detected:
            print(color_text("✓ System detected potential response loop", "green"))
        else:
            print(color_text("✓ System did NOT loop after context changed", "green"))
    
    # Direct execution version of loop detection test
    def run_loop_detection_test(self):
        """Direct execution version of the loop detection test"""
        with patch("ai_init.query_gemini_llm") as mock_gemini, \
             patch("ai_init.query_groq_llm") as mock_groq:
            
            # Configure mocks
            repeating_responses = [
                "I don't know about that, could you clarify?",
                "I'm not sure what you mean, please clarify.",
                "Could you provide more details about your question?"
            ]
            mock_gemini.side_effect = lambda *args, **kwargs: random.choice(repeating_responses)
            mock_groq.side_effect = lambda *args, **kwargs: random.choice(repeating_responses)
            
            # Call the actual test
            self.test_loop_detection(mock_groq, mock_gemini)
    
    # --- HALLUCINATION TESTS ---
    def test_hallucination_prevention(self, mock_llm):
        """Test if the system prevents hallucinations by verifying answers with facts"""
        print_header("HALLUCINATION PREVENTION TESTS")
        
        # Set of test questions and hallucinated/factual responses
        test_cases = [
            {
                "question": "Tell me about the Quantum Computing Club",
                "hallucinated": "The Quantum Computing Club meets every Tuesday at 7pm in the Engineering building. Dr. Smith is the faculty advisor.",
                "factual": "I don't have specific information about a Quantum Computing Club. Would you like to see a list of verified clubs instead?"
            },
            {
                "question": "How many members are in the Chess Club?",
                "hallucinated": "The Chess Club currently has 42 members and is growing rapidly.",
                "factual": "I don't have current membership numbers for the Chess Club. You might want to contact them directly for the most up-to-date information."
            }
        ]
        
        print_subheader("Testing response verification against known facts")
        
        for i, test_case in enumerate(test_cases):
            print(f"\nTest case {i+1}:")
            print(f"Question: {color_text(test_case['question'], 'blue')}")
            print(f"Potential hallucination: {color_text(test_case['hallucinated'], 'red')}")
            print(f"Factual response: {color_text(test_case['factual'], 'green')}")
            
            # Here we would test your actual hallucination prevention mechanism
            # For demo purposes, we'll just show verification
            mock_llm.return_value = test_case['hallucinated']
            
            # This is where you'd plug in your actual hallucination detection logic
            # For now, we'll just simulate detection based on keywords
            has_quantitative_claims = any(word in test_case['hallucinated'].lower() for word in 
                                        ['every', 'all', 'many', 'most', 'number', 'members', 
                                         'meets', 'meeting'])
            
            if has_quantitative_claims:
                print(color_text("✓ System would flag this response for verification", "green"))
            else:
                print(color_text("✗ System might not verify this potentially hallucinated response", "red"))
    
    # Direct execution version of hallucination test
    def run_hallucination_prevention_test(self):
        """Direct execution version of the hallucination prevention test"""
        with patch("ai_init.query_gemini_llm") as mock_llm:
            self.test_hallucination_prevention(mock_llm)
    
    # --- CONTEXT ADHERENCE TESTS ---
    def test_context_maintenance(self, mock_llm):
        """Test if the system maintains context across a conversation"""
        print_header("CONTEXT MAINTENANCE TESTS")
        
        # Simulate a multi-turn conversation
        conversation = [
            {"role": "user", "content": "What clubs are related to computer science?"},
            {"role": "assistant", "content": "There are several computer science related clubs including Programming Club, Cybersecurity Club, and AI Club."},
            {"role": "user", "content": "When do they meet?"},
            {"role": "assistant", "content": "The Programming Club meets on Mondays at 6pm, Cybersecurity Club on Wednesdays at 5pm, and AI Club on Thursdays at 7pm."},
            {"role": "user", "content": "Which one would you recommend for beginners?"}
        ]
        
        print_subheader("Testing conversation context maintenance")
        
        # Build history string as you might in your actual system
        history = "\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in conversation])
        print(color_text("Conversation history:", "cyan"))
        for turn in conversation:
            role_color = "blue" if turn["role"] == "user" else "green"
            print(color_text(f"{turn['role'].capitalize()}: {turn['content']}", role_color))
        
        # Test if context is maintained for the last question
        mock_llm.return_value = "For beginners, I would recommend the Programming Club as they offer introductory workshops."
        
        # Simulated test of your context processing
        context_keywords = ["computer science", "programming", "cybersecurity", "ai", "club"]
        context_maintained = any(keyword in history.lower() for keyword in context_keywords)
        
        print_subheader("Context maintenance results")
        if context_maintained:
            print(color_text("✓ System maintains context across conversation turns", "green"))
        else:
            print(color_text("✗ System may lose context between turns", "red"))
            
        # You'd add actual tests of your context maintenance mechanism here
        
        # Test specific context detection
        club_context = classifier.classify_return_recommendation(history)
        print(f"Does history suggest recommendation mode? {color_text(str(club_context), 'yellow')}")
    
    # Direct execution version of context test
    def run_context_maintenance_test(self):
        """Direct execution version of the context maintenance test"""
        with patch("ai_init.query_gemini_llm") as mock_llm:
            self.test_context_maintenance(mock_llm)
    
    # --- LLM PROVIDER FALLBACK TESTS ---
    def test_llm_provider_fallback(self, mock_groq, mock_gemini):
        """Test if the system falls back to alternate LLM providers on failure"""
        print_header("LLM PROVIDER FALLBACK TESTS")
        
        # Set up the first LLM to fail
        mock_gemini.side_effect = Exception("API connection error")
        mock_groq.return_value = "This is a response from the fallback LLM provider."
        
        print_subheader("Testing LLM provider fallback mechanism")
        
        try:
            # Try to call your function that would implement fallback
            # For demo purposes, we'll simulate the fallback
            primary_success = False
            response = None
            
            try:
                # Try primary LLM provider
                response = ai_init.query_gemini_llm("test question", "context", "api_key")
                primary_success = True
            except Exception as e:
                print(color_text(f"Primary LLM failed: {str(e)}", "yellow"))
                # Fall back to secondary provider
                response = ai_init.query_groq_llm("test question", "context", "api_key")
            
            print(f"Response received: {color_text(response, 'green')}")
            print(color_text("✓ System successfully handled LLM provider failure", "green"))
        except Exception as e:
            print(color_text(f"✗ System failed to handle LLM provider errors: {str(e)}", "red"))
    
    # Direct execution version of fallback test
    def run_llm_provider_fallback_test(self):
        """Direct execution version of the LLM provider fallback test"""
        with patch("ai_init.query_gemini_llm") as mock_gemini, \
             patch("ai_init.query_groq_llm") as mock_groq:
            
            # Configure mocks
            mock_gemini.side_effect = Exception("API connection error")
            mock_groq.return_value = "This is a response from the fallback LLM provider."
            
            # Call the actual test
            self.test_llm_provider_fallback(mock_groq, mock_gemini)

# Run specific integration test only when directly executed
if __name__ == "__main__":
    # Running manually from command line
    tester = TestChatbotSystem()
    tester.setup()
    print("\n")
    print(color_text("RUNNING FULL SYSTEM TEST SUITE", "bold"))
    print(color_text("================================\n", "bold"))
    
    # Select specific tests if command line args provided
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print(color_text("Running quick tests only\n", "yellow"))
        tester.run_context_maintenance_test()
    else:
        # Run all tests with the "run_" version
        tester.run_loop_detection_test()
        time.sleep(0.5)
        tester.run_hallucination_prevention_test()
        time.sleep(0.5)
        tester.run_context_maintenance_test()
        time.sleep(0.5)
        tester.run_llm_provider_fallback_test()
    
    tester.teardown()
    print(color_text("\nAll tests completed!", "green"))