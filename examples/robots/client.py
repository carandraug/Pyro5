import sys
import random
import Pyro5.config
from Pyro5.api import expose, oneway, SerializerBase, Daemon, Proxy
import robot
import remote


Pyro5.config.SERVERTYPE = "multiplex"  # to make sure all calls run in the same thread


class DrunkenGameObserver(remote.GameObserver):
    @oneway
    @expose
    def world_update(self, iteration, world, robotdata):
        # change directions randomly
        if random.random() > 0.8:
            if random.random() >= 0.5:
                dx, dy = random.randint(-1, 1), 0
            else:
                dx, dy = 0, random.randint(-1, 1)
            if random.random() > 0.7:
                self.robot.emote("..Hic! *burp*")
            self.robot.change_direction((dx, dy))


class AngryGameObserver(remote.GameObserver):
    def __init__(self):
        super(AngryGameObserver, self).__init__()
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # clockwise motion
        self.directioncounter = 0

    @oneway
    @expose
    def world_update(self, iteration, world, robotdata):
        # move in a loop yelling angry stuff
        if iteration % 50 == 0:
            self.robot.emote("I'll kill you all! GRR")
        if iteration % 10 == 0:
            self.directioncounter = (self.directioncounter + 1) % 4
            self.robot.change_direction(self.directions[self.directioncounter])


class ScaredGameObserver(remote.GameObserver):
    def __init__(self):
        super(ScaredGameObserver, self).__init__()
        # run to a corner
        self.direction = random.choice([(-1, -1), (1, -1), (1, 1), (-1, 1)])

    @oneway
    @expose
    def start(self):
        super(ScaredGameObserver, self).start()
        self.robot.change_direction(self.direction)

    @oneway
    @expose
    def world_update(self, iteration, world, robotdata):
        if iteration % 50 == 0:
            self.robot.emote("I'm scared!")


observers = {
    "drunk": DrunkenGameObserver,
    "angry": AngryGameObserver,
    "scared": ScaredGameObserver,
}


# register the Robot class with Pyro's serializers:
SerializerBase.register_class_to_dict(robot.Robot, robot.Robot.robot_to_dict)
SerializerBase.register_dict_to_class("robot.Robot", robot.Robot.dict_to_robot)


def main(args):
    if len(args) != 3:
        print("usage: client.py <robotname> <robottype>")
        print("   type is one of: %s" % list(observers.keys()))
        return
    name = args[1]
    observertype = args[2]
    with Daemon() as daemon:
        observer = observers[observertype]()
        daemon.register(observer)
        gameserver = Proxy("PYRONAME:example.robotserver")
        robot = gameserver.register(name, observer)
        with robot:   # make sure it disconnects, before the daemon thread uses it later
            robot.emote("Hi there! I'm here to kick your ass")
        observer.robot = robot
        print("Pyro server registered on %s" % daemon.locationStr)
        daemon.requestLoop()


if __name__ == "__main__":
    main(sys.argv)
