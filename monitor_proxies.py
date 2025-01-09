import yaml
import os
import re
import argparse
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProxiesHandler(FileSystemEventHandler):
    def __init__(self, clash_dir, output_dir):
        self.proxy_dir = os.path.join(clash_dir, 'proxies')
        self.output_dir = output_dir
        self.update_proxies()

    def on_modified(self, event):
        if event.src_path.endswith('.yaml') or event.src_path.endswith('.yml'):
            self.update_proxies()

    def is_ip_address(self, address):
        # 只匹配IPv4地址
        ipv4_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return re.match(ipv4_pattern, address) is not None

    def normalize_domain(self, domain):
        # 分割域名部分
        parts = domain.split('.')
        # 最多保留最后4级
        return '.'.join(parts[-4:])

    def get_all_servers(self):
        domains = set()
        ips = set()
        for root, _, files in os.walk(self.proxy_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    try:
                        with open(os.path.join(root, file), 'r') as f:
                            data = yaml.safe_load(f)
                            for proxy in data.get('proxies', []):
                                if 'server' in proxy:
                                    server = proxy['server']
                                    # 忽略IPv6地址
                                    if ':' in server:
                                        continue
                                    if self.is_ip_address(server):
                                        ips.add(server)
                                    else:
                                        domains.add(self.normalize_domain(server))
                    except Exception as e:
                        logging.error(f"Error reading {file}: {str(e)}")
        return domains, ips

    def update_proxies(self):
        try:
            domains, ips = self.get_all_servers()

            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)

            # 写入域名文件
            domain_file = os.path.join(self.output_dir, 'proxy.server.txt')
            with open(domain_file, 'w') as f:
                f.write('\n'.join(sorted(domains)))

            # 写入IP文件
            ip_file = os.path.join(self.output_dir, 'proxy.ip.txt')
            with open(ip_file, 'w') as f:
                f.write('\n'.join(sorted(ips)))

            logging.info(f"Updated {domain_file} with {len(domains)} unique domains")
            logging.info(f"Updated {ip_file} with {len(ips)} unique IPs")

            # 重启 mosdns 服务
            os.system('systemctl restart mosdns')
            logging.info("Restarted mosdns service")

        except Exception as e:
            logging.error(f"Error updating proxies: {str(e)}")

if __name__ == "__main__":
    # 配置路径
    parser = argparse.ArgumentParser(description='Monitor proxy YAML files and generate server lists')
    parser.add_argument(
        '--clash_dir',
        default='/data/router-aio/clash-meta',
        help='Clash directory containing proxies YAML files (default: /data/router-aio/clash-meta)')
    parser.add_argument(
        '--output_dir',
        default='/data/router-aio/MosDNS-Config/rules',
        help='Output directory for generated files (default: /data/router-aio/MosDNS-Config/rules)')
    args = parser.parse_args()

    # 创建监控器
    event_handler = ProxiesHandler(args.clash_dir, args.output_dir)
    observer = Observer()
    observer.schedule(event_handler, path=args.clash_dir, recursive=True)
    observer.start()

    try:
        logging.info(f"Monitoring {args.clash_dir} for changes...")
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
