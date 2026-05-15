import sys
f = 'supportagent/sop_engine.py'
content = open(f).read()

methods = '''
    def get_workflow_by_category(self, category: str):
        if category == 'urgent': return self.get_workflow('escalation_flow')
        if category == 'unknown': return self.get_workflow('general_flow')
        return self.get_workflow(f"{category}_flow") or self.get_workflow('general_flow')

    def get_workflow_by_name(self, name: str):
        return self.get_workflow(name)

    def get_workflow_for_ticket(self, ticket):
        cat = ticket.category.value if hasattr(ticket.category, 'value') else ticket.category
        if not cat: return self.get_workflow('general_flow')
        return self.get_workflow_by_category(cat)

    def get_workflow_steps(self, workflow):
        if not workflow: return []
        return workflow.steps

    def get_next_step(self, workflow, current_step_id):
        if not workflow or not workflow.steps: return None
        for i, s in enumerate(workflow.steps):
            if s.id == current_step_id:
                return workflow.steps[i+1] if i+1 < len(workflow.steps) else None
        return workflow.steps[0]

    def execute_workflow(self, workflow, ticket):
        if not workflow: return WorkflowExecution(execution_id='error', ticket_id=ticket.ticket_id, workflow_name='none')
        return self.execute(workflow.name, ticket)
'''

if 'get_workflow_by_category' not in content:
    open(f, 'w').write(content.replace('    def get_all_workflows', methods + '\n    def get_all_workflows'))
