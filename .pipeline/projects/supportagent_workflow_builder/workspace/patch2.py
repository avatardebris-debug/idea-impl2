f = 'tests/test_sop_engine.py'
c = open(f).read()
c = c.replace('in sop_engine.workflows]', 'in sop_engine.workflows.values()]')
c = c.replace('for workflow in sop_engine.workflows:', 'for workflow in sop_engine.workflows.values():')
open(f, 'w').write(c)

f2 = 'supportagent/sop_engine.py'
c2 = open(f2).read()
c2 = c2.replace('if not os.path.exists(self.workflows_dir):\n            return', 'if not os.path.exists(self.workflows_dir):\n            raise FileNotFoundError(f"Dir not found: {self.workflows_dir}")')
open(f2, 'w').write(c2)
