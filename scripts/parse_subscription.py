#!/usr/bin/env python3
"""订阅链接解析脚本。

该脚本负责从订阅 URL 下载并解析节点信息，支持多种订阅格式。

功能:
    - 从环境变量获取订阅 URL
    - 下载并解码订阅内容
    - 解析多种协议节点（VMess、VLESS、SS、Trojan 等）
    - 将解析结果保存为 JSON 文件供后续使用

环境变量:
    SUBSCRIPTION_URL: 订阅链接地址

输出:
    output/nodes.json: 解析后的节点列表
"""

import base64
import json
import os
import re
import sys
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests


def decode_subscription_content(content: str) -> str:
    """解码订阅内容。

    订阅内容通常使用 Base64 编码，此函数尝试多种解码方式。

    Args:
        content: 原始订阅内容字符串。

    Returns:
        解码后的内容字符串。

    Example:
        >>> decode_subscription_content("dm1lc3M6Ly9...")
        'vmess://...'
    """
    content = content.strip()
    
    try:
        decoded = base64.b64decode(content).decode('utf-8')
        if decoded.startswith(('vmess://', 'vless://', 'ss://', 'trojan://')):
            return decoded
    except Exception:
        pass
    
    try:
        padding = 4 - len(content) % 4
        if padding != 4:
            content += '=' * padding
        decoded = base64.urlsafe_b64decode(content).decode('utf-8')
        return decoded
    except Exception:
        pass
    
    return content


def parse_vmess_link(link: str) -> dict[str, Any] | None:
    """解析 VMess 协议链接。

    Args:
        link: VMess 协议链接，格式为 vmess://base64_json。

    Returns:
        解析后的节点配置字典，解析失败返回 None。

    Example:
        >>> parse_vmess_link("vmess://eyJhZGQiOiAiMTI3LjAuMC4xIiwgInBvcnQiOiAiNDQzIn0=")
        {'type': 'vmess', 'server': '127.0.0.1', 'port': 443, ...}
    """
    try:
        encoded = link.replace('vmess://', '')
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += '=' * padding
        
        decoded = base64.urlsafe_b64decode(encoded).decode('utf-8')
        config = json.loads(decoded)
        
        node = {
            'type': 'vmess',
            'name': config.get('ps', config.get('add', 'VMess节点')),
            'server': config.get('add', ''),
            'port': int(config.get('port', 443)),
            'uuid': config.get('id', ''),
            'alterId': int(config.get('aid', 0)),
            'cipher': config.get('scy', 'auto'),
            'udp': True,
            'network': config.get('net', 'tcp'),
        }
        
        if config.get('net') == 'ws':
            node['ws-opts'] = {
                'path': config.get('path', '/'),
                'headers': {'Host': config.get('host', config.get('add', ''))}
            }
        elif config.get('net') == 'grpc':
            node['grpc-opts'] = {
                'grpc-service-name': config.get('path', '')
            }
        
        tls = config.get('tls', '')
        if tls == 'tls':
            node['tls'] = True
            sni = config.get('sni') or config.get('host', '')
            if sni:
                node['servername'] = sni
        
        return node
    except Exception as e:
        print(f"解析 VMess 链接失败: {e}")
        return None


def parse_vless_link(link: str) -> dict[str, Any] | None:
    """解析 VLESS 协议链接。

    Args:
        link: VLESS 协议链接，格式为 vless://uuid@server:port?params#name。

    Returns:
        解析后的节点配置字典，解析失败返回 None。

    Example:
        >>> parse_vless_link("vless://uuid@127.0.0.1:443?type=tcp#节点")
        {'type': 'vless', 'server': '127.0.0.1', 'port': 443, ...}
    """
    try:
        parsed = urlparse(link)
        query = parse_qs(parsed.query)
        
        node = {
            'type': 'vless',
            'name': parsed.fragment or 'VLESS节点',
            'server': parsed.hostname or '',
            'port': parsed.port or 443,
            'uuid': parsed.username or '',
            'udp': True,
            'network': query.get('type', ['tcp'])[0],
        }
        
        if node['network'] == 'ws':
            node['ws-opts'] = {
                'path': query.get('path', ['/'])[0],
                'headers': {'Host': query.get('host', [node['server']])[0]}
            }
        elif node['network'] == 'grpc':
            node['grpc-opts'] = {
                'grpc-service-name': query.get('serviceName', [''])[0]
            }
        
        if query.get('security', [''])[0] == 'tls':
            node['tls'] = True
            sni = query.get('sni', [query.get('host', [node['server']])[0]])[0]
            if sni:
                node['servername'] = sni
        
        flow = query.get('flow', [''])[0]
        if flow:
            node['flow'] = flow
        
        return node
    except Exception as e:
        print(f"解析 VLESS 链接失败: {e}")
        return None


def parse_ss_link(link: str) -> dict[str, Any] | None:
    """解析 Shadowsocks 协议链接。

    Args:
        link: SS 协议链接，格式为 ss://base64(method:password)@server:port#name。

    Returns:
        解析后的节点配置字典，解析失败返回 None。

    Example:
        >>> parse_ss_link("ss://YWVzLTEyOC1nY206cGFzc3dvcmQ=@127.0.0.1:8388#SS节点")
        {'type': 'ss', 'server': '127.0.0.1', 'port': 8388, ...}
    """
    try:
        link = link.replace('ss://', '')
        
        from urllib.parse import unquote
        name = ''
        if '#' in link:
            link, name = link.rsplit('#', 1)
            name = unquote(name)
        
        if '@' in link:
            userinfo, serverinfo = link.rsplit('@', 1)
            try:
                decoded = base64.urlsafe_b64decode(userinfo + '==').decode('utf-8')
                method, password = decoded.split(':', 1)
            except Exception:
                method, password = userinfo.split(':', 1) if ':' in userinfo else ('aes-128-gcm', userinfo)
        else:
            try:
                decoded = base64.urlsafe_b64decode(link + '==').decode('utf-8')
                if '@' in decoded:
                    userinfo, serverinfo = decoded.rsplit('@', 1)
                    method, password = userinfo.split(':', 1)
                else:
                    return None
            except Exception:
                return None
        
        server, port = serverinfo.rsplit(':', 1) if ':' in serverinfo else (serverinfo, '8388')
        
        node = {
            'type': 'ss',
            'name': name or 'SS节点',
            'server': server,
            'port': int(port),
            'cipher': method,
            'password': password,
            'udp': True,
        }
        
        return node
    except Exception as e:
        print(f"解析 SS 链接失败: {e}")
        return None


def parse_trojan_link(link: str) -> dict[str, Any] | None:
    """解析 Trojan 协议链接。

    Args:
        link: Trojan 协议链接，格式为 trojan://password@server:port?params#name。

    Returns:
        解析后的节点配置字典，解析失败返回 None。

    Example:
        >>> parse_trojan_link("trojan://pass@127.0.0.1:443?sni=example.com#节点")
        {'type': 'trojan', 'server': '127.0.0.1', 'port': 443, ...}
    """
    try:
        parsed = urlparse(link)
        query = parse_qs(parsed.query)
        
        node = {
            'type': 'trojan',
            'name': parsed.fragment or 'Trojan节点',
            'server': parsed.hostname or '',
            'port': parsed.port or 443,
            'password': parsed.username or '',
            'udp': True,
            'skip-cert-verify': False,
        }
        
        sni = query.get('sni', [query.get('peer', [node['server']])[0]])[0]
        if sni:
            node['sni'] = sni
        
        network = query.get('type', ['tcp'])[0]
        if network == 'ws':
            node['network'] = 'ws'
            node['ws-opts'] = {
                'path': query.get('path', ['/'])[0],
                'headers': {'Host': query.get('host', [node['server']])[0]}
            }
        elif network == 'grpc':
            node['network'] = 'grpc'
            node['grpc-opts'] = {
                'grpc-service-name': query.get('serviceName', [''])[0]
            }
        
        return node
    except Exception as e:
        print(f"解析 Trojan 链接失败: {e}")
        return None


def parse_subscription(subscription_url: str) -> list[dict[str, Any]]:
    """解析订阅链接并返回节点列表。

    Args:
        subscription_url: 订阅链接地址。

    Returns:
        解析后的节点配置列表。

    Raises:
        requests.RequestException: 网络请求失败时抛出。

    Example:
        >>> nodes = parse_subscription("https://example.com/subscribe")
        >>> len(nodes)
        10
    """
    headers = {
        'User-Agent': 'ClashForWindows/0.20.39',
        'Accept': '*/*',
    }
    
    response = requests.get(subscription_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    content = response.text
    decoded_content = decode_subscription_content(content)
    
    nodes: list[dict[str, Any]] = []
    lines = decoded_content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        node = None
        if line.startswith('vmess://'):
            node = parse_vmess_link(line)
        elif line.startswith('vless://'):
            node = parse_vless_link(line)
        elif line.startswith('ss://'):
            node = parse_ss_link(line)
        elif line.startswith('trojan://'):
            node = parse_trojan_link(line)
        
        if node:
            nodes.append(node)
    
    return nodes


def main() -> int:
    """主函数入口。

    Returns:
        退出码，0 表示成功，非 0 表示失败。
    """
    subscription_url = os.environ.get('SUBSCRIPTION_URL', '')
    
    if not subscription_url:
        print("错误: 未设置 SUBSCRIPTION_URL 环境变量")
        return 1
    
    print(f"正在获取订阅: {subscription_url[:50]}...")
    
    try:
        nodes = parse_subscription(subscription_url)
        print(f"成功解析 {len(nodes)} 个节点")
        
        os.makedirs('output', exist_ok=True)
        
        with open('output/nodes.json', 'w', encoding='utf-8') as f:
            json.dump(nodes, f, ensure_ascii=False, indent=2)
        
        print("节点信息已保存到 output/nodes.json")
        return 0
        
    except Exception as e:
        print(f"解析订阅失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
