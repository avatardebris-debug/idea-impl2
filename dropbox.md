# Pipeline Dropbox

Steer the running pipeline, revise active projects, or add details while the runner is up.
The runner checks this file every **10 minutes**. The manager triages new entries and may reply below.

## How to post

Add a block like this at the **bottom** of the file:

```
### USER msg-20260520-001
target: project_slug_optional
Your message: steer, revise, add requirements, pause, reprioritize, etc.
```

- `target:` optional — project slug under `.pipeline/projects/<slug>/`
- Use unique ids: `msg-YYYYMMDD-NNN`

Manager replies appear as `### MANAGER msg-...-r1` blocks.
If the manager needs clarification, it will ask in a MANAGER block — reply with a new USER block referencing the same target.

---

