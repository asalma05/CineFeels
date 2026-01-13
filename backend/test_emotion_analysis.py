"""
Test BERT emotion analysis
"""
from services.emotion_service import get_emotion_analyzer
from models.emotion import EmotionScores


def print_emotions(emotions: EmotionScores, title: str = ""):
    """Pretty print emotions"""
    if title:
        print(f"\n{title}")
        print("=" * 60)

    print(f"  Joy:      {emotions.joy:.3f} {'█' * int(emotions.joy * 20)}")
    print(f"  Sadness:  {emotions.sadness:.3f} {'█' * int(emotions.sadness * 20)}")
    print(f"  Fear:     {emotions.fear:.3f} {'█' * int(emotions.fear * 20)}")
    print(f"  Anger:    {emotions.anger:.3f} {'█' * int(emotions.anger * 20)}")
    print(f"  Surprise: {emotions.surprise:.3f} {'█' * int(emotions.surprise * 20)}")
    print(f"  Disgust:  {emotions.disgust:.3f} {'█' * int(emotions.disgust * 20)}")
    print(f"  Neutral:  {emotions.neutral:.3f} {'█' * int(emotions.neutral * 20)}")


def test_basic_emotions():
    """Test BERT on basic emotion examples"""
    print("\n" + "=" * 70)
    print("🎬 CineFeels - BERT Emotion Analysis Test")
    print("=" * 70)

    # Initialize analyzer
    print("\n📥 Loading BERT model...")
    analyzer = get_emotion_analyzer()
    print("✅ Model loaded!\n")

    # Test cases
    test_cases = [
        {
            "text": "This movie was absolutely amazing! I loved every minute of it. The acting was superb and the story kept me engaged throughout.",
            "expected": "joy"
        },
        {
            "text": "This film was terrifying! I couldn't sleep for days. The suspense and horror elements were brilliantly executed.",
            "expected": "fear"
        },
        {
            "text": "I was so disappointed. The movie was boring and predictable. What a waste of time and money.",
            "expected": "sadness/anger"
        },
        {
            "text": "The plot twist at the end completely shocked me! I did not see that coming at all. Mind-blowing!",
            "expected": "surprise"
        },
        {
            "text": "This movie made me laugh so hard! The comedy was perfect and the jokes landed every time.",
            "expected": "joy"
        },
        {
            "text": "The ending made me cry. Such a beautiful and emotional story about love and loss.",
            "expected": "sadness"
        },
        {
            "text": "This action movie kept me on the edge of my seat! The chase scenes were incredible and thrilling.",
            "expected": "fear/surprise (thrill)"
        }
    ]

    # Analyze each test case
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        expected = test_case["expected"]

        print(f"\nTest {i}: {expected.upper()}")
        print("-" * 70)
        print(f"Text: \"{text[:100]}...\"")

        emotions = analyzer.analyze_text(text)
        print_emotions(emotions)

        # Find dominant emotion
        emotion_dict = emotions.to_dict()
        dominant = max(emotion_dict, key=emotion_dict.get)
        score = emotion_dict[dominant]

        print(f"\n  ➡️  Dominant: {dominant.upper()} ({score:.3f})")


def test_movie_reviews():
    """Test on actual movie reviews"""
    print("\n\n" + "=" * 70)
    print("🎬 Testing on Movie Review Examples")
    print("=" * 70)

    analyzer = get_emotion_analyzer()

    # Sample movie reviews
    reviews = {
        "Inception": [
            "A masterpiece of cinema! Christopher Nolan has created something truly special. The visual effects are stunning and the story is mind-bending.",
            "I was confused throughout the entire movie. Too complicated and pretentious.",
            "Absolutely brilliant! The dream sequences were beautifully crafted. One of the best films I've ever seen."
        ],
        "The Exorcist": [
            "Terrifying! I had nightmares for weeks. The scariest movie ever made.",
            "A horror classic that still holds up today. The atmosphere is incredibly disturbing.",
            "Too intense for me. I had to look away during several scenes."
        ],
        "Toy Story": [
            "A heartwarming tale about friendship and growing up. Made me tear up at the end.",
            "Perfect for kids and adults alike. Funny, touching, and beautifully animated.",
            "Such a joyful movie! My children loved it and so did I."
        ]
    }

    for movie_title, movie_reviews in reviews.items():
        print(f"\n{'=' * 70}")
        print(f"Movie: {movie_title}")
        print(f"{'=' * 70}")

        # Analyze reviews
        profile = analyzer.analyze_reviews(movie_reviews)

        print(f"\n📊 Emotion Profile (based on {profile.reviews_analyzed} reviews):")
        print_emotions(profile.base_emotions)

        print(f"\n🎯 CineFeels Emotions:")
        print(f"  Thrill:       {profile.thrill:.3f} {'█' * int(profile.thrill * 20)}")
        print(f"  Romance:      {profile.romance:.3f} {'█' * int(profile.romance * 20)}")
        print(f"  Inspiration:  {profile.inspiration:.3f} {'█' * int(profile.inspiration * 20)}")
        print(f"  Humor:        {profile.humor:.3f} {'█' * int(profile.humor * 20)}")

        print(f"\n  ➡️  Dominant Emotion: {profile.dominant_emotion.upper()}")


def test_performance():
    """Test analysis performance"""
    print("\n\n" + "=" * 70)
    print("⚡ Performance Test")
    print("=" * 70)

    import time

    analyzer = get_emotion_analyzer()

    # Test text
    text = "This movie was absolutely amazing! I loved every minute of it."

    # Warm-up
    analyzer.analyze_text(text)

    # Time multiple analyses
    num_tests = 10
    start_time = time.time()

    for _ in range(num_tests):
        analyzer.analyze_text(text)

    end_time = time.time()
    avg_time = (end_time - start_time) / num_tests

    print(f"\n✅ Analyzed {num_tests} texts")
    print(f"   Average time per text: {avg_time:.3f} seconds")
    print(f"   Throughput: {1/avg_time:.1f} texts/second")


if __name__ == "__main__":
    # Run all tests
    test_basic_emotions()
    test_movie_reviews()
    test_performance()

    print("\n\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70 + "\n")
