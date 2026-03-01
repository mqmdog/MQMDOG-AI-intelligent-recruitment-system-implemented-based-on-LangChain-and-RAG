#这是用来创建单例模式
from threading import Lock

class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """
    _instances = {} #存储每个类的唯一实例
    _lock: Lock = Lock() #线程锁，确保线程安全

    def __call__(cls, *args, **kwargs):  # 拦截类的实例化过程
        with cls._lock:
            if cls not in cls._instances: #如果类不在实例字典中，则创建实例并存储在字典中
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls] #返回缓存的实例