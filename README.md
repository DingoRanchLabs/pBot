# pBot

Version 0.1.31

Warning: This project is pre version 1!




## Development <a name="development"></a>

### Application Structure

pBot is broken into 3 services.

- **Admin** - web UI for bot administration and experimentation (see sandbox).
- **Listener** - handles interactions with discord. Collects incoming messages, sends any responses.
- **Bot** - the bot proper. Evaluates messages. Conditionally makes calls to AI.

```
                             ┌──────────┐
                             │ Discord  │
                             └──────────┘
                                   ▲
               ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
                Docker             ▼
               │              ┌────────┐               │
                              │Listener│
               │              │Service │               │
                              └────────┘
               │                   ▲                   │
┌──────────┐                       │
│  OpenAI  │◀─┐│  ┌────────┐       ▼       ┌────────┐  │
└──────────┘  │   │  Bot   │    ┌─────┐    │ Admin  │
              ├┼─▶│Service │◀──▶│Redis│◀──▶│Service │  │
┌──────────┐  │   └────────┘    └─────┘    └────────┘
│Midjourney│◀─┘│                                       │
└──────────┘    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
```

### Model Structure

.

### Dependencies

#### Python

| Dependency | Admin Service | Bot Service | Listener Service |
|:---|:---:|:---:|:---:|
| [discord](https://discordpy.readthedocs.io/en/stable/) | | | &#x2705; |
| [Flask](https://flask.palletsprojects.com/en/3.0.x/) | &#x2705; | | |
| [openai](https://pypi.org/project/openai/) | | &#x2705; | |
| [pylint](https://pypi.org/project/pylint/) | &#x2705; | &#x2705; | &#x2705; |
| [pytest](https://docs.pytest.org/en/8.0.x/) | &#x2705; | &#x2705; | &#x2705; |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | &#x2705; | &#x2705; | &#x2705; |
| [ratelimit](https://pypi.org/project/ratelimit/) | | &#x2705; | &#x2705; |
| [tiktoken](https://pypi.org/project/tiktoken/) | | &#x2705; | |
| [redis-py](https://redis-py.readthedocs.io/en/stable/) | &#x2705; | &#x2705; | &#x2705; |

#### Front-End

| Dependency | Admin Service | Bot Service | Listener Service |
|:---|:---:|:---:|:---:|
| [Bootstrap 5](https://getbootstrap.com/) | &#x2705; | | |

### Contributing

Fork & submit a pull request. I'll try to reply quickly. :pray:

#### Design Philosophy

While there is stil much to do, pBot is meant to be a simple bot framework on which you can experiment and build. Dependencies and patterns have been chosen to this end. <ins>Always keep the novice developer in mind.</ins> As tempting as it might be to write *clever* code, doing so probably wont do newer developers any favors.

#### Code Quality

- Write code for humans first, machines second.
- Comments should explain why, not how.
- Code should be written as
self-documenting as possible.
- Code should have tests behind it and those tests must pass!
- Pylint should pass 100%. You can ignore a rule if there is a good reason (dependency causes ignorable issue) but document why.

### Helpful Third Party Documentation

#### OpenAI

- [API Documentation](https://platform.openai.com/docs/overview)
- [OpenAI Cookbook](https://cookbook.openai.com/)
- [Developer Forums](https://community.openai.com/)
- [Pricing](https://openai.com/pricing)
- [Rate limits](https://platform.openai.com/docs/guides/rate-limits?context=tier-free)
- [Prompt engineering guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Best practices for prompt engineering](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)
- [Tokens](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them)

#### Discord

- [Discord Developer Portal](https://discord.com/developers)
- [discord.py](https://discordpy.readthedocs.io/en/stable/index.html)
- [Rate limits](https://discord.com/developers/docs/topics/rate-limits)

#### Midjourney

- [docs.midjourney.com](https://docs.midjourney.com/docs/quick-start)

#### Future Bard Stuff

- [https://aibard.online/bard-api-documentation/](https://aibard.online/bard-api-documentation/)
- [https://github.com/ra83205/google-bard-api](https://github.com/ra83205/google-bard-api)

#### Misc.

- [Semantic versioning](https://semver.org/)

### TODO:

- Handle a monthly token allotment. Ration AI responses for both openai and midjourney.
- Image "mirroring"
- More robust multi-call decision making?
- rate limiting
- Incite chaos!
- document invoke usage
- trim old redis lists by message expiry:
  - messages
  - user:9:messages
  - channel:7:messages
  - server:5:messages


.
