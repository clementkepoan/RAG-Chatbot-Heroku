import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from ai_init import query_groq_llm, query_openrouter_llm
from classifier import classify_question
from faq_formatter import format_faqs_for_llm_club, context_website_student, context_website_manager

# Load environment variables
load_dotenv()

# Get API keys
GROQ_API_KEY = "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"
OPENROUTER_API_KEY = "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"

# Configurationç
CLUB_ID = "4798d2b6-073b-4428-96a2-1a0e6184f7ed"
USER_ID = "none"

# Test questions covering different classifications
test_questions = [
    # Club questions
    "What activities does this club organize?",
    "When is the next meeting scheduled?",
    "What are the membership requirements for this club?",
    
    # Website questions
    "How do I reset my password on the website?",
    "How do I update my profile picture?",
    "How can I change my notification settings?",
    
    # Both/Ambiguous questions
    "How do I sign up for club events through the website?",
    "I want to join this club and attend the upcoming event, what steps should I take?",
    "How can I contact the club president through the platform?",
    "Where can I find photos from past club events?"
]

def test_with_provider(provider="openrouter"):
    """Test questions using the specified provider"""
    results = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"Testing question {i}/{len(test_questions)} with {provider}...")
        
        try:
            # Get classification
            start_time = time.time()
            classification = classify_question(question,provider)
            
            # Choose appropriate context based on classification
            if classification == "Club":
                context_text = format_faqs_for_llm_club(CLUB_ID, USER_ID)
            elif classification == "Website":
                context_text = context_website_student()
            elif classification == "Both":
                context_text = format_faqs_for_llm_club(CLUB_ID, USER_ID) + context_website_student()
            else:
                context_text = "You are a helpful assistant."
            
            # Query LLM based on provider
            if provider == "groq":
                answer = query_groq_llm(question, context_text, GROQ_API_KEY)
            else:
                answer = query_openrouter_llm(question, context_text, OPENROUTER_API_KEY)
            
            end_time = time.time()
            
            # Store results
            results.append({
                "question": question,
                "classification": classification,
                "answer": answer,
                "response_time": round(end_time - start_time, 2),
                "status": "Success"
            })
                
        except Exception as e:
            print(f"Error: {str(e)}")
            results.append({
                "question": question,
                "status": f"Exception: {str(e)}",
                "response_time": 0
            })
        
        # Add delay to avoid rate limiting
        time.sleep(1)
    
    return results

def compare_results(openrouter_results, groq_results):
    """Compare results from both providers"""
    comparison = []
    
    for i in range(len(test_questions)):
        or_result = openrouter_results[i] if i < len(openrouter_results) else {}
        groq_result = groq_results[i] if i < len(groq_results) else {}
        
        comparison.append({
            "question": test_questions[i],
            "openrouter_classification": or_result.get("classification", "N/A"),
            "groq_classification": groq_result.get("classification", "N/A"),
            "classifications_match": or_result.get("classification") == groq_result.get("classification"),
            "openrouter_time": or_result.get("response_time", 0),
            "groq_time": groq_result.get("response_time", 0),
            "openrouter_status": or_result.get("status", "N/A"),
            "groq_status": groq_result.get("status", "N/A"),
            "openrouter_answer": or_result.get("answer", "N/A")[:100] + "..." if or_result.get("answer") else "N/A",
            "groq_answer": groq_result.get("answer", "N/A")[:100] + "..." if groq_result.get("answer") else "N/A"
        })
    
    return comparison

def save_results(openrouter_results, groq_results, comparison):
    """Save results to a file"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"direct_test_results_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write(f"Direct API Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("COMPARISON SUMMARY\n")
        f.write("-" * 80 + "\n")
        
        for i, comp in enumerate(comparison, 1):
            f.write(f"Question {i}: {comp['question']}\n")
            f.write(f"  Classification: {comp['openrouter_classification']}\n")
            f.write(f"  OpenRouter: ({comp['openrouter_time']}s) - {comp['openrouter_status']}\n")
            f.write(f"  Groq: ({comp['groq_time']}s) - {comp['groq_status']}\n")
            f.write(f"  OpenRouter Answer: {comp['openrouter_answer']}\n")
            f.write(f"  Groq Answer: {comp['groq_answer']}\n\n")
        
        # Add full answers in a separate section
        f.write("\nFULL ANSWERS\n")
        f.write("=" * 80 + "\n\n")
        
        for i, (or_result, groq_result) in enumerate(zip(openrouter_results, groq_results), 1):
            f.write(f"Question {i}: {or_result.get('question', 'N/A')}\n")
            f.write(f"Classification: {or_result.get('classification', 'N/A')}\n")
            f.write("-" * 80 + "\n")
            f.write("OpenRouter Answer:\n")
            f.write(f"{or_result.get('answer', 'N/A')}\n\n")
            f.write("Groq Answer:\n")
            f.write(f"{groq_result.get('answer', 'N/A')}\n\n")
            f.write("=" * 80 + "\n\n")
    
    print(f"Results saved to {filename}")
    return filename

def main():
    """Main test function"""
    print("Starting direct API tests...")
    
    # Temporarily fix the classifier to use OpenRouter for consistency
    # We're testing the LLM responses, not the classifier
    original_function = classify_question
    
    try:
        print("\nTesting with OpenRouter...")
        openrouter_results = test_with_provider("openrouter")
        
        print("\nTesting with Groq...")
        groq_results = test_with_provider("groq")
        
        print("\nComparing results...")
        comparison = compare_results(openrouter_results, groq_results)
        
        print("\nSaving results...")
        result_file = save_results(openrouter_results, groq_results, comparison)
        
        # Print summary
        match_count = sum(1 for comp in comparison if comp["classifications_match"])
        
        # Calculate average response times
        or_times = [r.get("response_time", 0) for r in openrouter_results if r.get("status") == "Success"]
        groq_times = [r.get("response_time", 0) for r in groq_results if r.get("status") == "Success"]
        
        or_avg = sum(or_times) / len(or_times) if or_times else 0
        groq_avg = sum(groq_times) / len(groq_times) if groq_times else 0
        
        print(f"\nTest completed!")
        print(f"OpenRouter average response time: {or_avg:.2f}s")
        print(f"Groq average response time: {groq_avg:.2f}s")
        print(f"Full results saved to {result_file}")
        
    finally:
        # Restore original classify function
        pass

if __name__ == "__main__":
    main()