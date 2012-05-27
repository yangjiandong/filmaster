import logging
logger = logging.getLogger(__name__)

import os
import pickle
import types

class Error(Exception):
  """Base class for exceptions in this module."""

class PermanentTaskFailure(Error):
  """Indicates that a task failed, and will never succeed."""

def run(data):
  """Unpickles and executes a task.

  Args:
    data: A pickled tuple of (function, args, kwargs) to execute.
  Returns:
    The return value of the function invocation.
  """
  try:
    func, args, kwds = pickle.loads(data)
  except Exception, e: 
    raise PermanentTaskFailure(e)
  else:
    return func(*args, **kwds)

def invoke_member(obj, membername, *args, **kwargs):
  """Retrieves a member of an object, then calls it with the provided arguments.

  Args:
    obj: The object to operate on.
    membername: The name of the member to retrieve from ojb.
    args: Positional arguments to pass to the method.
    kwargs: Keyword arguments to pass to the method.
  Returns:
    The return value of the method invocation.  
  """
  return getattr(obj, membername)(*args, **kwargs)

def _curry_callable(obj, *args, **kwargs):
  """Takes a callable and arguments and returns a task queue tuple.

  The returned tuple consists of (callable, args, kwargs), and can be pickled
  and unpickled safely.

  Args:
    obj: The callable to curry. See the module docstring for restrictions.
    args: Positional arguments to call the callable with.
    kwargs: Keyword arguments to call the callable with. 
  Returns:
    A tuple consisting of (callable, args, kwargs) that can be evaluated by
    run() with equivalent effect of executing the function directly.
  Raises:
    ValueError: If the passed in object is not of a valid callable type.
  """
  if isinstance(obj, types.MethodType):
    return (invoke_member, (obj.im_self, obj.im_func.__name__) + args, kwargs)
  elif isinstance(obj, types.BuiltinMethodType):
    if not obj.__self__:
      return (obj, args, kwargs)
    else:
      return (invoke_member, (obj.__self__, obj.__name__) + args, kwargs)
  elif isinstance(obj, types.ObjectType) and hasattr(obj, "__call__"):   
    return (obj, args, kwargs)
  elif isinstance(obj, (types.FunctionType, types.BuiltinFunctionType,
                        types.ClassType, types.UnboundMethodType)):   
    return (obj, args, kwargs)
  else:
    raise ValueError("obj must be callable")

def serialize(obj, *args, **kwargs):
  """Serializes a callable into a format recognized by the deferred executor. 

  Args:
    obj: The callable to serialize. See module docstring for restrictions.
    args: Positional arguments to call the callable with.
    kwargs: Keyword arguments to call the callable with.
  Returns:
    A serialized representation of the callable.
  """
  curried = _curry_callable(obj, *args, **kwargs)
  return pickle.dumps(curried, protocol=pickle.HIGHEST_PROTOCOL)  

from django.conf import settings
def defer(obj, *args, **kwargs):
  """Defers a callable for execution later.

  Args:
    obj: The callable to execute. See module docstring for restrictions.
    _countdown, _eta, _name, _transactional, _url, _queue: Passed through to
    the task queue - see the task queue documentation for details.
    args: Positional arguments to call the callable with.
    kwargs: Any other keyword arguments are passed through to the callable.
  Returns:
    A taskqueue.Task object which represents an enqueued callable.
  """
  delay = kwargs.pop('_delay', None)
  if delay:
      import datetime
      kwargs['_eta'] = datetime.datetime.now() + datetime.timedelta(seconds=delay)

  taskargs = dict((x, kwargs.pop(("_%s" % x), None))
                  for x in ("countdown", "eta", "routing_key", "priority", "exchange"))

  taskargs.setdefault('routing_key', settings.CELERY_DEFAULT_QUEUE)

  func, args, kw = _curry_callable(obj, *args, **kwargs)

  logger.debug("defer: %r %r %r", func, args, kw)

  try:
      from tasks import DeferredTask
      DeferredTask.apply_async(args=(func,args,kwargs), **taskargs)
  except Exception, e:
      logger.warning(unicode(e))
