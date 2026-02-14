#!/usr/bin/env python3
"""Clash 配置生成脚本。

该脚本根据解析的节点信息生成完整的 Clash 配置文件。

功能:
    - 读取解析后的节点 JSON 文件
    - 根据模板生成 Clash 配置
    - 支持自定义规则和代理组
    - 生成订阅转换后的配置文件

输入:
    output/nodes.json: 解析后的节点列表

输出:
    output/clash.yaml: Clash 配置文件
    output/clash_pro.yaml: Clash Meta 配置文件
"""

import json
import os
import sys
from typing import Any

import yaml


def load_template() -> dict[str, Any]:
    """加载 Clash 配置模板。

    Returns:
        配置模板字典。

    Example:
        >>> template = load_template()
        >>> 'proxies' in template
        True
    """
    template_path = 'templates/clash_template.yaml'
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    return get_default_template()


def get_default_template() -> dict[str, Any]:
    """获取默认配置模板。

    Returns:
        默认配置字典，包含基础配置、代理组和规则。

    Example:
        >>> template = get_default_template()
        >>> template['port']
        7890
    """
    return {
        'port': 7890,
        'socks-port': 7891,
        'mixed-port': 7892,
        'allow-lan': True,
        'bind-address': '*',
        'mode': 'rule',
        'log-level': 'info',
        'ipv6': False,
        'external-controller': '127.0.0.1:9090',
        'dns': {
            'enable': True,
            'ipv6': False,
            'enhanced-mode': 'fake-ip',
            'fake-ip-range': '198.18.0.1/16',
            'fake-ip-filter': [
                '*.lan',
                '*.local',
                '*.localhost',
                '*.localhost.localdomain',
                '*.localdomain',
                'localhost.ptlogin2.qq.com',
                '+.stun.*.*',
                '+.stun.*.*.*',
                '+.stun.*.*.*.*',
                '+.stun.*.*.*.*.*',
                'lens.l.google.com',
                'stun.l.google.com',
                'time.windows.com',
                'time.nist.gov',
                'time.apple.com',
                'time.asia.apple.com',
                'ntp.ubuntu.com',
            ],
            'nameserver': [
                '223.5.5.5',
                '119.29.29.29',
                '1.1.1.1',
                '8.8.8.8',
            ],
            'fallback': [
                'tls://1.1.1.1:853',
                'tls://8.8.8.8:853',
            ],
            'fallback-filter': {
                'geoip': True,
                'geoip-code': 'CN',
                'ipcidr': ['240.0.0.0/4'],
            },
        },
        'proxy-groups': [
            {
                'name': '🚀 节点选择',
                'type': 'select',
                'proxies': ['♻️ 自动选择', '🇭🇰 香港节点', '🇨🇳 台湾节点', '🇸🇬 狮城节点', '🇯🇵 日本节点', '🇺🇸 美国节点', 'DIRECT'],
            },
            {
                'name': '♻️ 自动选择',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'proxies': [],
            },
            {
                'name': '🇭🇰 香港节点',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'proxies': [],
            },
            {
                'name': '🇨🇳 台湾节点',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'proxies': [],
            },
            {
                'name': '🇸🇬 狮城节点',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'proxies': [],
            },
            {
                'name': '🇯🇵 日本节点',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'proxies': [],
            },
            {
                'name': '🇺🇸 美国节点',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'proxies': [],
            },
            {
                'name': '🎯 全球直连',
                'type': 'select',
                'proxies': ['DIRECT', '🚀 节点选择'],
            },
            {
                'name': '🛑 全球拦截',
                'type': 'select',
                'proxies': ['REJECT', 'DIRECT'],
            },
            {
                'name': '🐟 漏网之鱼',
                'type': 'select',
                'proxies': ['🚀 节点选择', '🎯 全球直连', '♻️ 自动选择'],
            },
        ],
        'rules': [
            'DOMAIN-SUFFIX,local,🎯 全球直连',
            'IP-CIDR,127.0.0.0/8,🎯 全球直连',
            'IP-CIDR,172.16.0.0/12,🎯 全球直连',
            'IP-CIDR,192.168.0.0/16,🎯 全球直连',
            'IP-CIDR,10.0.0.0/8,🎯 全球直连',
            'GEOIP,CN,🎯 全球直连',
            'MATCH,🐟 漏网之鱼',
        ],
    }


def classify_node(node: dict[str, Any]) -> str:
    """根据节点名称分类节点。

    Args:
        node: 节点配置字典。

    Returns:
        节点所属分类标识。

    Example:
        >>> classify_node({'name': '香港 01'})
        'hk'
    """
    name = node.get('name', '').lower()
    
    keywords_map: dict[str, list[str]] = {
        'hk': ['香港', 'hk', 'hongkong', 'hong kong', '港'],
        'tw': ['台湾', 'tw', 'taiwan', '台'],
        'sg': ['新加坡', 'sg', 'singapore', '狮城'],
        'jp': ['日本', 'jp', 'japan', '东京', '大阪'],
        'us': ['美国', 'us', 'usa', 'united states', '美'],
        'kr': ['韩国', 'kr', 'korea', '首尔'],
    }
    
    for region, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword in name:
                return region
    
    return 'other'


def generate_clash_config(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """生成完整的 Clash 配置。

    Args:
        nodes: 节点配置列表。

    Returns:
        完整的 Clash 配置字典。

    Example:
        >>> config = generate_clash_config([{'type': 'ss', 'name': 'Test', ...}])
        >>> len(config['proxies'])
        1
    """
    config = load_template()
    config['proxies'] = nodes
    
    proxy_names = [node['name'] for node in nodes]
    
    region_nodes: dict[str, list[str]] = {
        'hk': [],
        'tw': [],
        'sg': [],
        'jp': [],
        'us': [],
        'other': [],
    }
    
    for node in nodes:
        region = classify_node(node)
        region_nodes[region].append(node['name'])
    
    for group in config.get('proxy-groups', []):
        if group['name'] == '♻️ 自动选择':
            group['proxies'] = proxy_names.copy()
        elif group['name'] == '🇭🇰 香港节点':
            group['proxies'] = region_nodes['hk'].copy() if region_nodes['hk'] else proxy_names[:1] if proxy_names else []
        elif group['name'] == '🇨🇳 台湾节点':
            group['proxies'] = region_nodes['tw'].copy() if region_nodes['tw'] else proxy_names[:1] if proxy_names else []
        elif group['name'] == '🇸🇬 狮城节点':
            group['proxies'] = region_nodes['sg'].copy() if region_nodes['sg'] else proxy_names[:1] if proxy_names else []
        elif group['name'] == '🇯🇵 日本节点':
            group['proxies'] = region_nodes['jp'].copy() if region_nodes['jp'] else proxy_names[:1] if proxy_names else []
        elif group['name'] == '🇺🇸 美国节点':
            group['proxies'] = region_nodes['us'].copy() if region_nodes['us'] else proxy_names[:1] if proxy_names else []
    
    return config


def generate_meta_config(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """生成 Clash Meta 配置。

    Clash Meta 支持更多协议，如 VLESS、Hysteria 等。

    Args:
        nodes: 节点配置列表。

    Returns:
        Clash Meta 配置字典。

    Example:
        >>> config = generate_meta_config([{'type': 'vless', 'name': 'Test', ...}])
        >>> 'proxies' in config
        True
    """
    config = generate_clash_config(nodes)
    
    config['geodata-mode'] = True
    config['geox-url'] = {
        'geoip': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/geoip.dat',
        'geosite': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/geosite.dat',
        'mmdb': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/geoip@release/Country.mmdb',
    }
    
    config['sniffer'] = {
        'enable': True,
        'sniff': {
            'HTTP': {'ports': [80, '8080-8880'], 'override-destination': True},
            'TLS': {'ports': [443, 8443]},
            'QUIC': {'ports': [443, 8443]},
        },
    }
    
    return config


def main() -> int:
    """主函数入口。

    Returns:
        退出码，0 表示成功，非 0 表示失败。
    """
    nodes_path = 'output/nodes.json'
    
    if not os.path.exists(nodes_path):
        print(f"错误: 节点文件不存在: {nodes_path}")
        return 1
    
    with open(nodes_path, 'r', encoding='utf-8') as f:
        nodes = json.load(f)
    
    if not nodes:
        print("错误: 没有可用的节点")
        return 1
    
    print(f"正在生成 Clash 配置，共 {len(nodes)} 个节点...")
    
    os.makedirs('output', exist_ok=True)
    
    clash_config = generate_clash_config(nodes)
    with open('output/clash.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(clash_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print("已生成 output/clash.yaml")
    
    meta_config = generate_meta_config(nodes)
    with open('output/clash_meta.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(meta_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print("已生成 output/clash_meta.yaml")
    
    subscription_content = ''
    with open('output/clash.yaml', 'r', encoding='utf-8') as f:
        subscription_content = f.read()
    
    import base64
    encoded = base64.b64encode(subscription_content.encode('utf-8')).decode('utf-8')
    with open('output/subscription.txt', 'w', encoding='utf-8') as f:
        f.write(encoded)
    print("已生成 output/subscription.txt")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
