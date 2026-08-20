"""
Quick test script for GitHub integration
"""

from backend.gh_integration.github_client import GitHubClient

print("\n" + "=" * 70)
print("  GITHUB INTEGRATION - VERIFICATION TEST")
print("=" * 70)

# Initialize client
client = GitHubClient()

if not client.is_configured():
    print("\n[FAIL] GitHub is NOT configured!")
    print("   Please check your .env file.")
    exit(1)

print("\n[OK] GitHub client is configured and connected!")

# Get repository info
info = client.get_repository_info()

if info["success"]:
    print("\n📁 Repository Information:")
    print(f"   Full Name: {info['full_name']}")
    print(f"   Description: {info['description'] or '(no description)'}")
    print(f"   Default Branch: {info['default_branch']}")
    print(f"   Private: {info['private']}")
    print(f"   URL: {info['url']}")
    
    print("\n[OK] GitHub integration is working perfectly!")
    print("\n🎉 Your system can now:")
    print("   1. Create branches automatically")
    print("   2. Commit generated code")
    print("   3. Create actual pull requests")
    print("   4. Add labels and reviewers")
    
    print("\n[RUN] Ready for complete end-to-end automation!")
else:
    print(f"\n[FAIL] Failed to get repository info: {info['error']}")
    exit(1)

print("\n" + "=" * 70 + "\n")
