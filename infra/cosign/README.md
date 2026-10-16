# Cosign image-signing keys

The Jenkins pipeline signs every image it builds with [cosign](https://github.com/sigstore/cosign)
and refuses to pass a build whose images do not verify against this
directory's public key. Design and threat model: `docs/SCOPE_DECISIONS.md`.

## Where each key lives

| Item | Location | In git? |
|---|---|---|
| Public key `cosign.pub` | `infra/cosign/cosign.pub` (this directory) | **Yes** - verifying needs only the public key, and anyone may read it |
| Private key `cosign.key` | Jenkins credential, kind **Secret file**, ID `cosign-private-key` | **No** - `*.key` is in `.gitignore` |
| Private key password | Jenkins credential, kind **Secret text**, ID `cosign-password` | **No** |

The private key is encrypted with the password (cosign uses scrypt +
secretbox), so a leaked `cosign.key` file alone cannot sign. Both
credentials are injected only into the signing stage via `withCredentials`,
and Jenkins masks them in console output.

## One-time setup (on the EC2 host that runs Jenkins + Minikube)

```bash
# 1. Generate the pair inside the repo checkout (cosign.key is git-ignored here)
cd ~/enterprise-quantum-computing-platform/infra/cosign
cosign generate-key-pair          # prompts for a password - remember it for step 2

# 2. Add both credentials in Jenkins:
#    Manage Jenkins -> Credentials -> System -> Global credentials -> Add Credentials
#      Kind: Secret file   ID: cosign-private-key   File: cosign.key
#      Kind: Secret text   ID: cosign-password      Secret: <the password>

# 3. Remove the private key from disk - Jenkins now holds the only copy
shred -u cosign.key

# 4. Commit ONLY the public key
git add cosign.pub
git status --short                # must show cosign.pub and nothing ending in .key
git commit -m "Add cosign public key for image signature verification"
git push
```

Until `cosign.pub` is committed, the pipeline's verify stage fails closed
(it stops the build rather than skipping verification).

## Rotation / compromise

If the private key or its password may have leaked: generate a new pair,
replace both Jenkins credentials, commit the new `cosign.pub`, and re-run
the pipeline. Images signed with the old key then fail verification,
because the pipeline only trusts the committed public key.
