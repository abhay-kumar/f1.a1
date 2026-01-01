# Contributing to F1.ai

Thank you for your interest in contributing to F1.ai!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/f1.a1.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Test your changes with a sample project
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature`
8. Open a Pull Request

## Development Setup

```bash
# Install dependencies
pip install requests google-auth-oauthlib google-api-python-client
brew install ffmpeg yt-dlp  # macOS

# Set up test credentials
mkdir -p shared/creds
echo "your-test-api-key" > shared/creds/elevenlabs
```

## Code Style

- Use Python 3.10+ features
- Follow PEP 8 conventions
- Keep modules focused on single responsibility
- Add docstrings for public functions
- Use descriptive variable names

## Pull Request Guidelines

- Keep PRs focused on a single change
- Update README.md if adding new features
- Test the full pipeline before submitting
- Describe what your PR does and why

## Areas for Contribution

- **New video effects** - Additional FFmpeg filters and transitions
- **Platform support** - TikTok, Instagram Reels upload support
- **Voice options** - Additional TTS providers or voice configurations
- **Footage sources** - Alternative video sources beyond YouTube
- **Caption styles** - New text animation or styling options
- **Performance** - Faster encoding, parallel processing

## Reporting Issues

When reporting bugs, please include:
- Python version
- ffmpeg version (`ffmpeg -version`)
- Operating system
- Error message and stack trace
- Steps to reproduce

## Questions?

Open an issue with the "question" label.
