'''
This code is part of Cosmic Commando; Copyright (C) 2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.game_data import game
from guts.messages import infotip, message
from guts.debug import debug

class Objective(object):
    
    INTERACT = 'INTERACT'
    KILL = 'KILL'
    ARRIVE = 'ARRIVE'
    FETCH = 'FETCH'
    DELIVER = 'DELIVER'
    SPOT = 'SPOT'
    USE = 'USE'
    USE_ON = 'USE ON'
    FLAG = 'FLAG' #for a number of turns
    #AGGREGATE = 'AGGREGATE' #TODO: to get a bunch of optional objectives turned into one not-optional. Maybe this should be quest chains, though. 
    
    def __init__(self, oid, description_todo, description_done, kind, target, prereqs = [], repeats = 1, retroactive = True, optional = False, negative = False):
        self.id = oid
        self._description_todo = description_todo
        self._description_done = description_done 
        self.prereqs = prereqs
        self.kind = kind
        self.target = target
        self.repeats = repeats
        self.accomplished = 0
        self.optional = optional
        self._available = not prereqs
        self.retroactive = retroactive
        self._negative = negative
    
    def _get_description(self):
        if self.is_fulfilled():
            return self._description_done
        else:
            progress = ""
            if self.repeats > 1:
                progress = " {0}/{1}".format(self.accomplished, self.repeats)
            desc = "{0}{1}".format(self._description_todo, progress)
            return desc
    description = property(_get_description)
    
    def is_optional(self):
        return self.optional
    
    def is_available(self):
        return self._available

    def is_negative(self):
        return self._negative

    def _set_available(self, value):
        self._available = value
        if value:
            self.set_progress_threshold()
    available = property(is_available, _set_available)

    def is_fulfilled(self):
        return self.accomplished >= self.repeats    

    def _get_status(self):
        if self.is_fulfilled():
            return 'fulfilled'
        if self.is_available():
            return 'available'
        else:
            return 'unavailable'
    status = property(_get_status)
    
    def set_progress_threshold(self):
        if self.kind == self.__class__.KILL:
            self._progress_threshold = 0 if self.retroactive else game.kill_list[self.target]
        elif self.kind == self.__class__.ARRIVE:
            self._progress_threshold = 0
        elif self.kind == self.__class__.FETCH:
            self._progress_threshold = 0
        elif self.kind == self.__class__.DELIVER:
            self._progress_threshold = 0            
        elif self.kind == self.__class__.INTERACT:
            self._progress_threshold = 0
        elif self.kind == self.__class__.SPOT:
            self._progress_threshold = 0 #TODO: if retroactive else (number of spotted things in fov at the moment)
        elif self.kind == self.__class__.USE:
            self._progress_threshold = 0
        elif self.kind == self.__class__.USE_ON:
            self._progress_threshold = 0 #TODO: if retroactive else (number of uses on a valid target?)
        elif self.kind == self.__class__.FLAG:
            self._progress_threshold = 0
            #retroactive or not, because turns being flagged before the objective is active cannot be measured yet
        else:
            debug.log("Unknown kind of objective: {0}. Objective id: {1}".format(self.kind, self.id))
    
    def check_progress(self):
        accomplishment_so_far = self.accomplished
        progress = False
        if self.kind == self.__class__.KILL:
            self.accomplished = game.kill_list[self.target] - self._progress_threshold
            progress = self.accomplished > accomplishment_so_far 
        elif self.kind == self.__class__.ARRIVE:
            pass
        elif self.kind == self.__class__.FETCH:
            pass
        elif self.kind == self.__class__.DELIVER:
            pass            
        elif self.kind == self.__class__.INTERACT:
            pass
        elif self.kind == self.__class__.SPOT:
            #TODO: change to tiles in fov and check for features, items & terrain
            #TODO: compare to threshold? change threshold to a list?
            for agent in game.agents_in_sight:
                if agent.name == self.target:
                    self.accomplished +=1
                    progress = True
        elif self.kind == self.__class__.USE:
            pass
        elif self.kind == self.__class__.USE_ON:
            for item in game.player.inventory:
                if item.name == self.target[0]:
                    if 'last target' in item:
                        if item['last target'].name == self.target[1]:
                            self.accomplished +=1
                            progress = True
        elif self.kind == self.__class__.FLAG:
            if game.player.flag(self.target):
                self.accomplished += 1
                progress = True
        else:
            debug.log("Unknown kind of objective: {0}. Objective id: {1}".format(self.kind, self.id))
        if progress:
            if self._negative:
                message("{0} {1}.".format("You have failed an objective: " if self.is_fulfilled() else "You're closer to failing the objective: ",
                                     self.description),'failure' if self.is_fulfilled() else 'warning')
            else:
                message("{0} {1}.".format("You have fulfilled an objective: " if self.is_fulfilled() else "You make progress on objective: ",
                                     self.description),'completed quest' if self.is_fulfilled() else 'tracked quest')
        return progress
    
    def __repr__(self):
        return ','.join([str(self.__class__),self.id, self.description, str(self.prereqs), str(self.kind), str(self.repeats), str(self.accomplished), str(self.optional)])

class Quest(object):
    '''
    classdocs
    '''

    INACTIVE = 'inactive'
    ACTIVE = 'active'
    CURRENT = 'current'
    COMPLETED = 'completed'
    FAILED = 'failed'

    def __init__(self, name, description, outcomes, status = 'active', acquisition_message = None):
        '''
        * name to refer to the quest by
        * description to display in the HUD/quest selection info
        * objectives to complete during the quest (in a dictionary)
        * status - one of the enumerated states quest can have 
        '''
        self.name = name
        self.description = description
        self.outcomes = outcomes
        self._status = status
        self.objectives = {}
        self._successful = None
        self.acquisition_message = acquisition_message
    
    def is_completed(self):
        return self._status == self.__class__.COMPLETED
    
    def is_failed(self):
        return self._status == self.__class__.FAILED

    def is_active(self):
        return self._status == self.__class__.ACTIVE

    def is_inactive(self):
        return self._status == self.__class__.INACTIVE
    
    def add_goal(self, objective):
        self.objectives[objective.id] = objective
    
    def get_goal(self, objective_id):
        return self.objectives[objective_id]

    def _get_status(self):
        return self._status
    
    def _set_status(self, value):
        self._status = value
        if value == self.__class__.CURRENT:
            for objective in [objective for objective in list(self.objectives.values()) if objective.status == 'available']:
                objective.set_progress_threshold()
    status = property(_get_status, _set_status)
        
    def complete(self):
        """ This is a proper place to put in hooks for quest manipulation.
            or is it?
            TODO: handling of quest trees (but for now the idea is to make 100% non-linear games)
        """
        self._status = self.__class__.COMPLETED
    
    def fail(self):
        self._status = self.__class__.FAILED    
    
    def is_finished(self):
        incomplete = False
        for objective in list(self.objectives.values()):
            if objective.is_negative() and objective.is_fulfilled() and not objective.is_optional():
                self._successful = False
                return True
            elif not objective.is_optional() and not objective.is_fulfilled() and not objective.is_negative():
                incomplete = True
        if incomplete:
            return False
        else:
            self._successful = True
            return True
    
    def _check_finish(self):
        if self.is_finished():
            if self._successful:
                self.complete()
            else:
                self.fail()
    
    def update_availability_of_objectives(self):
        for objective in list(self.objectives.values()):
            if objective.prereqs and not objective.is_available():
                make_available = True
                for objective_id in objective.prereqs:
                    if not self.objectives[objective_id].is_fulfilled():
                        make_available = False
                        break
                objective.available = make_available

    def accomplish(self, objective_id):
        self.objectives[objective_id].accomplished += 1
        self.update_availability_of_objectives()
        self._check_finish()
                
    def progress_objectives(self):
        progress = False
        for objective in [objective for objective in list(self.objectives.values()) if objective.status == 'available']:
            if objective.check_progress():
                progress = True 
        if progress:
            self.update_availability_of_objectives()
            self._check_finish()
