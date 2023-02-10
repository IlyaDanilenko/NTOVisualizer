import sys, roslibpy
from argparse import ArgumentParser
from threading import Thread
from math import degrees, acos
from PyQt5.QtWidgets import QApplication, QMainWindow
from ObjectVisualizator.main import SettingsManager, VisualizationWorld, VisWidget

class ObjectServer:
    def __init__(self, visualization, hostname, port):
        self.visualization = visualization
        self.__create = False
        # self.hostname = hotname
        # self.port = port
        self.client = roslibpy.Ros(hostname, port)
        self.online = False
        self.__ros_thread = None

    def ros2panda(self, orientation):
        return degrees(acos(orientation['x']))

    def __change_drone_state(self, message):
        if not self.__create:
            self.visualization.add_model(
                'drone',
                (
                    message['pose']['position']['x'],
                    message['pose']['position']['y'],
                    message['pose']['position']['z']
                ),
                self.ros2panda(message['pose']['orientation'])
            )
            self.__create = True
        
        self.visualization.change_model_color(
            message['id'],
            message['color']['r'],
            message['color']['g'],
            message['color']['b']
        )

        self.visualization.change_model_position(
            message['id'],
            (
                message['pose']['position']['x'],
                message['pose']['position']['y'],
                message['pose']['position']['z']
            ),
            self.ros2panda(message['pose']['orientation'])
        )

    def __ros_target(self):
        drone_topic = roslibpy.Topic(self.client, "visualization_marker", "visualization_msgs/Marker")
        drone_topic.subscribe(self.__change_drone_state)

        while self.online:
            pass

        self.client.terminate()

    def close(self):
        self.online = False

    def run(self):
        try:
            self.client.run()
            self.online = True
            self.__ros_thread = Thread(target=self.__ros_target)

            self.__ros_thread.daemon = True
            self.__ros_thread.start()
        except roslibpy.core.RosTimeoutError:
            print("Не запущен ROS")

if __name__ == '__main__':
    settings = SettingsManager()
    settings.load("./settings/settings.json")
    world = VisualizationWorld(settings)
    server = ObjectServer(world, settings.server.ip, settings.server.port)
    
    app = QApplication(sys.argv)
    appw = QMainWindow()
    appw.setGeometry(50, 50, 800, 600)
    pandaWidget = VisWidget(world, appw, server)
    appw.setCentralWidget(pandaWidget)
    appw.show()

    server.run()
    
    sys.exit(app.exec_())