import json
import logging
from core.arguments import Argument
from core.filter import Filter
from core.flag import Flag
from .database import db, Base

logger = logging.getLogger(__name__)


class Triggers(Base):
    """
    ORM for the triggers in the Walkoff database
    """
    __tablename__ = "triggers"
    name = db.Column(db.String(255), nullable=False)
    playbook = db.Column(db.String(255), nullable=False)
    workflow = db.Column(db.String(255), nullable=False)
    condition = db.Column(db.String(255, convert_unicode=False), nullable=False)

    def __init__(self, name, playbook, workflow, condition):
        """
        Constructs a Trigger object
        
        Args:
            name (str): Name of the trigger object
            playbook (str): Playbook of the workflow to be connected to the trigger
            workflow (str): The workflow to be connected to the trigger
            condition (str): String of the JSON representation of the conditional to be checked by the trigger
        """
        self.name = name
        self.playbook = playbook
        self.workflow = workflow
        self.condition = condition

    def edit_trigger(self, form=None):
        """Edits a trigger
        
        Args:
            form (form, optional): Wtf-form containing the edited information
            
        Returns:
            True on successful edit, False otherwise.
        """
        if form:
            if form.name.data:
                self.name = form.name.data

            if form.playbook.data:
                self.playbook = form.playbook.data

            if form.playbook.data:
                self.workflow = form.workflow.data

            if form.conditional.data:
                try:
                    json.loads(form.conditional.data)
                    self.condition = form.conditional.data
                except ValueError:
                    return False
        return True

    def as_json(self):
        """ Gets the JSON representation of all the Trigger object.
        
        Returns:
            The JSON representation of the Trigger object.
        """
        return {'name': self.name,
                'conditions': json.loads(self.condition),
                'playbook': self.playbook,
                'workflow': self.workflow}

    @staticmethod
    def execute(data_in, input_in):
        """Tries to match the data_in against the conditionals of all the triggers registered in the database.
        
        Args:
            data_in (str): Data to be used to match against the conditionals
            input_in (str): The input to the first step of the workflow
            
        Returns:
            Dictionary of {"status": <status string>}
        """
        triggers = Triggers.query.all()
        from server.flaskserver import running_context
        for trigger in triggers:
            conditionals = json.loads(trigger.condition)
            if all(Triggers.__execute_trigger(conditional, data_in) for conditional in conditionals):
                workflow_to_be_executed = running_context.controller.get_workflow(trigger.playbook, trigger.workflow)
                if workflow_to_be_executed:
                    if input_in:
                        input_args = {arg['key']: Argument(key=arg['key'],
                                                           value=arg['value'],
                                                           format=arg.get('format', 'str'))
                                      for arg in input_in}
                        workflow_to_be_executed.execute(start_input=input_args)
                        logger.info('Workflow {0} executed with input {1}'.format(workflow_to_be_executed.name,
                                                                                  input_args))
                    else:
                        workflow_to_be_executed.execute()
                        logger.info('Workflow {0} executed with no input'.format(workflow_to_be_executed.name))
                    return {"status": "success"}
                else:
                    logger.error('Workflow associated with trigger is not in controller')
                    return {"status": "error: workflow could not be found"}
        logging.debug('No trigger matches data input')
        return {"status": "warning: no trigger found valid for data in"}

    @staticmethod
    def __execute_trigger(conditional, data_in):
        flag_args = {arg['key']: Argument(key=arg['key'],
                                          value=arg['value'],
                                          format=arg.get('format', 'str'))
                     for arg in conditional['args']}
        filters = [Filter(action=filter_element['action'],
                          args={arg['key']: Argument(key=arg['key'],
                                                     value=arg['value'],
                                                     format=arg.get('format', 'str'))
                                for arg in filter_element['args']}
                          )
                   for filter_element in conditional['filters']]
        return Flag(action=conditional['flag'], args=flag_args, filters=filters)(data_in)

    def __repr__(self):
        return json.dumps(self.as_json())

    def __str__(self):
        out = {'name': self.name,
               'conditions': json.loads(self.condition),
               'play': self.playbook}
        return json.dumps(out)
