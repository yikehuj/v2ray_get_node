import requests
import time
import urllib3
import argparse
import sys
import os
import configparser
import shlex  # 用于模拟命令行解析

# 关闭SSL安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = "config.ini"


def print_welcome_screen():
    """程序启动时的指令目录"""
    guide = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                📦 免费节点爬取工具 (交互模式)               ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ [可用指令]                                                 ┃
┃  show           查看当前 config.ini 中的配置信息           ┃
┃  set -o <路径>  临时修改本次运行的输出路径                 ┃
┃  set -p <代理>  临时修改并校验本次运行的代理               ┃
┃  run            开始执行爬取任务                           ┃
┃  run -o <路径>  指定路径并立即运行                         ┃
┃  help           显示此帮助菜单                             ┃
┃  exit           退出程序                                   ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 提示: 只有通过 'set' 或运行成功后的参数才会被保存到配置文件  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """
    print(guide)


def load_config():
    """读取配置，若不存在则初始化空结构"""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config['SETTINGS'] = {'output_path': '', 'proxy': '', 'urls': '', 'timeout': '10'}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
    config.read(CONFIG_FILE, encoding='utf-8')
    return config


def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        config.write(f)


def check_proxy_live(proxy_addr):
    """校验代理有效性"""
    proxies = {"http": proxy_addr, "https": proxy_addr}
    print(f"📡 正在校验代理: {proxy_addr}...")
    try:
        requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5, verify=False)
        print("✅ 代理有效")
        return True
    except:
        print("❌ 代理无效")
        return False


def execute_scrape(config, override_path=None, override_proxy=None):
    """核心抓取逻辑"""
    settings = config['SETTINGS']

    # 确定最终参数
    path = override_path or settings.get('output_path')
    proxy = override_proxy or settings.get('proxy')
    urls = [u.strip() for u in settings.get('urls', '').split(',') if u.strip()]

    # 强制校验必要项
    if not path:
        print("❌ 错误: 未设置输出路径，请先使用 'set -o' 设置。")
        return
    if not urls:
        print("❌ 错误: config.ini 中没有 URL 列表。")
        return

    print(f"\n🚀 任务启动 | 路径: {path} | 代理: {proxy or '直连'}")

    proxies_dict = {"http": proxy, "https": proxy} if proxy else None
    success = 0

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            for i, url in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}] 抓取: {url[:50]}...")
                try:
                    r = requests.get(url, proxies=proxies_dict, timeout=10, verify=False,
                                     headers={"User-Agent": "Mozilla/5.0"})
                    r.raise_for_status()
                    f.write(r.text + "\n\n")
                    success += 1
                except Exception as e:
                    print(f"   ❌ 失败: {str(e)[:30]}")
        print(f"\n✨ 抓取结束！成功: {success}, 失败: {len(urls) - success}")

        # 任务成功后，如果是通过参数临时指定的，询问是否保存
        if override_path or override_proxy:
            save = input("❓ 是否将本次使用的参数保存到配置文件? (y/n): ").lower()
            if save == 'y':
                if override_path: settings['output_path'] = override_path
                if override_proxy: settings['proxy'] = override_proxy
                save_config(config)
                print("💾 配置已更新。")

    except Exception as e:
        print(f"🚨 文件写入失败: {e}")


def main():
    config = load_config()
    print_welcome_screen()

    while True:
        try:
            # 获取用户输入并模拟命令行解析
            cmd_line = input("\n[节点工具] >>> ").strip()
            if not cmd_line: continue

            parts = shlex.split(cmd_line)
            cmd = parts[0].lower()

            if cmd == "exit":
                print("👋 再见！")
                break

            elif cmd == "help":
                print_welcome_screen()

            elif cmd == "show":
                s = config['SETTINGS']
                print("\n--- 当前配置 ---")
                print(f"📂 路径: {s.get('output_path')}")
                print(f"🌐 代理: {s.get('proxy')}")
                print(f"🔗 链接: {len(s.get('urls', '').split(','))} 个")

            elif cmd == "set":
                # 解析 set 指令的参数
                sub_parser = argparse.ArgumentParser(exit_on_error=False)
                sub_parser.add_argument("-o", "--output")
                sub_parser.add_argument("-p", "--proxy")
                sub_args = sub_parser.parse_args(parts[1:])

                if sub_args.output:
                    config['SETTINGS']['output_path'] = sub_args.output
                    save_config(config)
                    print(f"✅ 路径已永久更新: {sub_args.output}")

                if sub_args.proxy:
                    if check_proxy_live(sub_args.proxy):
                        config['SETTINGS']['proxy'] = sub_args.proxy
                        save_config(config)
                        print(f"✅ 代理已永久更新: {sub_args.proxy}")

            elif cmd == "run":
                # 解析 run 指令的可选临时参数
                sub_parser = argparse.ArgumentParser(exit_on_error=False)
                sub_parser.add_argument("-o", "--output")
                sub_parser.add_argument("-p", "--proxy")
                sub_args, unknown = sub_parser.parse_known_args(parts[1:])

                # 校验临时代理
                temp_proxy = sub_args.proxy
                if temp_proxy and not check_proxy_live(temp_proxy):
                    print("⚠️ 临时代理无效，放弃运行。")
                    continue

                execute_scrape(config, override_path=sub_args.output, override_proxy=temp_proxy)

            else:
                print(f"❌ 未知指令: {cmd}。输入 'help' 查看用法。")

        except KeyboardInterrupt:
            print("\n输入 'exit' 退出程序。")
        except Exception as e:
            print(f"❌ 指令解析错误: {e}")


if __name__ == "__main__":
    main()