# Python And Terminal Primer

这页不是完整 Python 教程。它只解释本课程马上会用到的东西，目标是让你不会被环境和语法拦在门口。

## Terminal

Terminal 就是用文字命令操作电脑的地方。课程里的命令默认从这个目录运行：

```bash
cd /Users/sunyibo/programs/study-agent/redesign
```

如果命令前面写着 `uv run`，意思是：用这个项目自己的 Python 环境运行命令，而不是随便拿系统里的 Python。

## Python Shell

Python shell 是一个可以一行一行输入 Python 的地方：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

进入后会看到类似 `>>>` 的提示符。你可以粘贴 Python 代码。退出时输入：

```python
exit()
```

## Why PYTHONPATH Exists Here

这个项目的代码在：

```text
packages/research_core/src
```

`pytest` 知道这个路径，因为 `pyproject.toml` 里配置了它。普通 Python shell 不知道，所以课程示例显式加上：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

如果忘了这段，最常见的错误是：

```text
ModuleNotFoundError: No module named 'research_core'
```

这不是你代码写坏了，只是 Python 没找到本地 package。

## import

`import` 是把别人写好的东西拿进当前文件或 shell：

```python
from research_core.runtime import AgentRunner
```

这句话的意思是：从 `research_core.runtime` 这个模块里拿出 `AgentRunner` 这个类。

## list And dict

课程里会经常看到 list：

```python
["model_request", "model_response"]
```

它表示一组有顺序的东西。

也会经常看到 dict：

```python
{"text": "hello"}
```

它表示一组 key-value。Agent tool 的输入输出必须能变成 JSON，所以课程里会尽量用字符串、数字、布尔值、list、dict 这些简单形状。

## lambda

这是一种很短的函数写法：

```python
lambda arguments: {"text": arguments["text"]}
```

在人话里就是：给我一个 `arguments`，我从里面拿出 `text`，再包装成 `{"text": ...}` 返回。

你也可以写成普通函数：

```python
def echo(arguments):
    return {"text": arguments["text"]}
```

两种写法在 lab 里效果一样。

## assert

`assert` 是学习和测试时很好用的检查方式：

```python
assert result.final_message.content == "final answer"
```

如果等号两边一样，程序继续。 如果不一样，Python 会抛出 `AssertionError`。这说明你的实际结果和预期不同，需要打印变量检查。

## try / except

有些练习会故意让程序报错，然后观察错误里带的事件：

```python
try:
    risky_operation()
except KeyError as exc:
    print(exc)
```

`try` 是“试着做这件事”。`except` 是“如果出现这种错误，就这样处理”。在 Agent 系统里，错误本身也要能被观察，不能只留下一个崩溃。

## Reading A Traceback

Traceback 是 Python 的报错堆栈。先别被它吓到，优先看最后两行：

```text
KeyError: "unknown tool 'missing'"
```

最后一行通常告诉你错误类型和核心原因。前面的文件路径和行号再用来定位是哪段代码触发的。

## Minimum Python You Need For Chapter 01

你不需要精通 Python，但需要能看懂：

- `from ... import ...`
- list 和 dict
- 函数调用，比如 `AgentRunner(...).run(...)`
- `lambda` 或 `def`
- `assert`
- `try / except`
- 打印变量：`print(...)`

如果这些还不熟，先不要急着理解 Agent。先把 lab 里的代码照着跑通，然后再回来看这些语法。
