

from model import get_test_build
from view import PuilderView


def execute_shell_action(projectpath, build, action):
    pass


if __name__ == '__main__':



    p = PuilderView()
    p.set_build(get_test_build())
    p.show_and_loop()
