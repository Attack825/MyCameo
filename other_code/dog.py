from injector import Injector, inject, singleton


# 定义 Animal 接口
class Animal:
    def speak(self) -> str:
        raise NotImplementedError


# 定义 Dog 和 Cat 类
class Dog(Animal):
    def speak(self) -> str:
        return "Woof!"


class Cat(Animal):
    def speak(self) -> str:
        return "Meow!"


# 定义一个服务类，依赖于 Animal
class AnimalService:
    @inject
    def __init__(self, animal: Animal):
        self.animal = animal

    def make_speak(self) -> None:
        print(self.animal.speak())


# 配置依赖注入
def configure(binder):
    binder.bind(Animal, to=Dog, scope=singleton)


# 创建 Injector 实例
injector = Injector([configure])

# 获取 AnimalService 实例
animal_service = injector.get(AnimalService)

# 调用方法
animal_service.make_speak()  # 输出: Woof!
