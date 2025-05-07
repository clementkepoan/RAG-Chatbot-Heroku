
from supabase_client import search_clubs_by_interest



def main():
    interest = "balls"
    results = search_clubs_by_interest(interest)
    print(f"Clubs related to {interest}:")
    
    print(results)

if __name__ == "__main__":
    main()

