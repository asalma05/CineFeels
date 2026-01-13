"""
Interactive emotion analysis - Test BERT on custom text
"""
from services.emotion_service import get_emotion_analyzer
from models.emotion import EmotionScores


def print_emotions(emotions: EmotionScores):
    """Pretty print emotions with bars"""
    print("\n📊 Emotion Analysis:")
    print("=" * 60)

    emotion_dict = emotions.to_dict()

    # Sort by score (highest first)
    sorted_emotions = sorted(emotion_dict.items(), key=lambda x: x[1], reverse=True)

    for emotion, score in sorted_emotions:
        bar = "█" * int(score * 40)
        percentage = score * 100
        print(f"  {emotion.capitalize():12} {percentage:5.1f}%  {bar}")

    print("=" * 60)

    # Dominant emotion
    dominant = sorted_emotions[0]
    print(f"\n  ➡️  Dominant: {dominant[0].upper()} ({dominant[1]:.3f})")

    # CineFeels emotions
    thrill = (emotions.fear + emotions.surprise) / 2
    romance = emotions.joy
    inspiration = (emotions.joy + emotions.surprise) / 2
    humor = emotions.joy

    print(f"\n🎯 CineFeels Emotions:")
    print(f"  Thrill:       {thrill:.3f}")
    print(f"  Romance:      {romance:.3f}")
    print(f"  Inspiration:  {inspiration:.3f}")
    print(f"  Humor:        {humor:.3f}")


def main():
    """Interactive text analysis"""
    print("\n" + "=" * 60)
    print("🎬 CineFeels - Interactive Emotion Analysis")
    print("=" * 60)

    # Load model
    print("\n📥 Loading BERT model...")
    analyzer = get_emotion_analyzer()
    print("✅ Model loaded!\n")

    # Example texts
    examples = [
        "This movie was absolutely terrifying!",
        "I laughed so hard during this comedy!",
        "The ending made me cry tears of joy.",
        "What a shocking plot twist!",
        "I was so disappointed and angry."
    ]

    print("💡 Try these examples:")
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")
    print()

    # Interactive loop
    while True:
        print("-" * 60)
        text = input("Enter text to analyze (or 'quit' to exit): ").strip()

        if text.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!\n")
            break

        if not text:
            print("❌ Please enter some text.\n")
            continue

        # Check if user entered a number (example)
        if text.isdigit() and 1 <= int(text) <= len(examples):
            text = examples[int(text) - 1]
            print(f"\nUsing example: \"{text}\"")

        # Analyze
        print(f"\n🔍 Analyzing: \"{text[:100]}...\"" if len(text) > 100 else f"\n🔍 Analyzing: \"{text}\"")

        emotions = analyzer.analyze_text(text)
        print_emotions(emotions)
        print()


if __name__ == "__main__":
    main()
