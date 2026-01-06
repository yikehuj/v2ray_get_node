import requests
import time
import urllib3
import argparse
import sys

# 关闭SSL安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def check_proxy_availability(proxy_config, timeout=10):
    """测试代理是否有效"""
    if not proxy_config:
        print("未配置代理，跳过代理测试\n", file=sys.stderr)
        return False

    print(f"正在测试代理：{proxy_config['http']}\n")
    try:
        resp_proxy = requests.get(
            url="https://httpbin.org/ip",
            proxies=proxy_config,
            timeout=timeout,
            verify=False
        )
        resp_proxy.raise_for_status()
        proxy_ip = resp_proxy.json()["origin"]

        resp_local = requests.get(
            url="https://httpbin.org/ip",
            timeout=timeout,
            verify=False
        )
        local_ip = resp_local.json()["origin"]

        if proxy_ip != local_ip:
            print(f"✅ 代理生效！代理IP：{proxy_ip}\n")
            return True
        else:
            print(f"❌ 代理未生效（IP未变化），本地IP：{local_ip}\n", file=sys.stderr)
            return False
    except Exception as e:
        print(f"❌ 代理测试失败：{str(e)}\n", file=sys.stderr)
        return False


def scrape_urls(url_list, file_path, use_proxy=False, proxy_config=None, timeout=10, total_timeout=60):
    """爬取URL列表并写入文件"""
    # 参数校验
    if not url_list:
        print("❌ 错误：URL列表为空，无需爬取", file=sys.stderr)
        return
    if not file_path:
        print("❌ 错误：文件路径未指定", file=sys.stderr)
        return

    with open(file_path, mode='w', encoding='utf-8', errors='replace') as f:
        total_start_time = time.time()
        success_count = 0

        for idx, url in enumerate(url_list, 1):
            if time.time() - total_start_time >= total_timeout:
                print(f"\n⏰ 整体爬取超时（{total_timeout}秒），终止任务", file=sys.stderr)
                break

            print(f"\n[{idx}/{len(url_list)}] 正在爬取：{url}")
            try:
                request_kwargs = {
                    "url": url,
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"
                    },
                    "timeout": timeout,
                    "verify": False
                }
                if use_proxy and proxy_config:
                    request_kwargs["proxies"] = proxy_config

                resp = requests.get(**request_kwargs)
                resp.raise_for_status()

                f.write(resp.text)
                f.write("\n\n")
                print(f"✅ 爬取成功：{url}")
                success_count += 1

            except requests.exceptions.Timeout:
                print(f"❌ 爬取超时：{url}（超时时间：{timeout}秒）", file=sys.stderr)
            except requests.exceptions.RequestException as e:
                print(f"❌ 爬取失败：{url} 错误：{str(e)[:50]}", file=sys.stderr)
            except Exception as e:
                print(f"❌ 未知错误：{url} 错误：{str(e)[:50]}", file=sys.stderr)

        print(f"\n📊 爬取完成：共{len(url_list)}个URL，成功{success_count}个，失败{len(url_list) - success_count}个")
        print(f"💾 结果已保存至：{file_path}")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="📦 免费节点爬虫命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  1. 基础使用（默认配置）：
     python node_scraper.py

  2. 自定义文件路径和代理：
     python node_scraper.py -o D:/nodes.txt -p socks5://127.0.0.1:10808

  3. 自定义URL列表（多个URL用逗号分隔）：
     python node_scraper.py -u "https://url1.txt,https://url2.txt"

  4. 不使用代理：
     python node_scraper.py --no-proxy
        """
    )

    # 核心参数
    parser.add_argument(
        "-o", "--output",
        default="D:/yikehuj/temp/free_get_node.txt",
        help="文件保存路径（默认：D:/yikehuj/temp/free_get_node.txt）"
    )
    parser.add_argument(
        "-p", "--proxy",
        default="socks5://127.0.0.1:10808",
        help="代理地址（格式：socks5://IP:端口 或 http://IP:端口，默认：socks5://127.0.0.1:10808）"
    )
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="不使用代理（优先级高于--proxy）"
    )
    parser.add_argument(
        "-u", "--urls",
        default="https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/yudou66.txt,"
                "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/blues.txt,"
                "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/clashmeta.txt,"
                "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/nodev2ray.txt,"
                "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/nodefree.txt,"
                "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/v2rayshare.txt,"
                "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/wenode.txt",
        help="待爬取的URL列表（多个URL用英文逗号分隔，默认使用内置列表）"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=10,
        help="单个请求超时时间（秒，默认：10）"
    )
    parser.add_argument(
        "-T", "--total-timeout",
        type=int,
        default=60,
        help="整体爬取超时时间（秒，默认：60）"
    )

    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()

    # 处理代理配置
    if args.no_proxy:
        proxy_config = None
    else:
        # 统一代理配置格式（适配http/https/socks5）
        proxy_config = {
            "http": args.proxy,
            "https": args.proxy
        }

    # 处理URL列表（拆分逗号分隔的字符串）
    url_list = [url.strip() for url in args.urls.split(",") if url.strip()]

    # 打印配置信息
    print("📋 当前配置：")
    print(f"  输出文件：{args.output}")
    print(f"  代理配置：{'不使用代理' if args.no_proxy else args.proxy}")
    print(f"  URL数量：{len(url_list)}")
    print(f"  单个请求超时：{args.timeout}秒")
    print(f"  整体超时：{args.total_timeout}秒\n")

    # 测试代理
    proxy_available = check_proxy_availability(proxy_config, args.timeout)

    # 开始爬取
    scrape_urls(
        url_list=url_list,
        file_path=args.output,
        use_proxy=proxy_available and not args.no_proxy,
        proxy_config=proxy_config,
        timeout=args.timeout,
        total_timeout=args.total_timeout
    )

    print("\n✅ 所有任务完成！")


if __name__ == "__main__":
    main()