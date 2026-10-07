"""Deployment profile generator (阿里云: 部署 profile).

生成 Dockerfile / docker-compose / K8s manifest 文本（不落盘，只返回字符串）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DeployProfile:
    service: str
    image: str
    port: int = 8000
    python_version: str = "3.11"
    env: Dict[str, str] = field(default_factory=dict)
    replicas: int = 1
    cpu: str = "500m"
    memory: str = "512Mi"

    def dockerfile(self) -> str:
        env_lines = "\n".join(
            f"ENV {k}={v}" for k, v in self.env.items()
        )
        return "\n".join([
            f"FROM python:{self.python_version}-slim",
            "WORKDIR /app",
            "COPY requirements.txt .",
            "RUN pip install --no-cache-dir -r requirements.txt",
            "COPY . .",
            env_lines,
            f"EXPOSE {self.port}",
            f'CMD ["python", "-m", "backend.__main__"]',
        ]).strip() + "\n"

    def compose(self) -> str:
        env_block = "\n".join(
            f"      {k}: {v}" for k, v in self.env.items()
        )
        return "\n".join([
            "version: '3.8'",
            "services:",
            f"  {self.service}:",
            f"    image: {self.image}",
            f"    ports:",
            f"      - \"{self.port}:{self.port}\"",
            "    environment:",
            env_block or "      {}",
        ]).strip() + "\n"

    def k8s_deployment(self) -> str:
        env_block = "\n".join(
            f"            - name: {k}\n              value: \"{v}\""
            for k, v in self.env.items()
        )
        return "\n".join([
            "apiVersion: apps/v1",
            "kind: Deployment",
            "metadata:",
            f"  name: {self.service}",
            "spec:",
            f"  replicas: {self.replicas}",
            "  selector:",
            "    matchLabels:",
            f"      app: {self.service}",
            "  template:",
            "    metadata:",
            "      labels:",
            f"        app: {self.service}",
            "    spec:",
            "      containers:",
            f"        - name: {self.service}",
            f"          image: {self.image}",
            "          resources:",
            "            requests:",
            f"              cpu: {self.cpu}",
            f"              memory: {self.memory}",
            "          env:",
            env_block or "            []",
            "          ports:",
            f"            - containerPort: {self.port}",
        ]).strip() + "\n"

    def k8s_service(self) -> str:
        return "\n".join([
            "apiVersion: v1",
            "kind: Service",
            "metadata:",
            f"  name: {self.service}",
            "spec:",
            "  selector:",
            f"    app: {self.service}",
            "  ports:",
            f"    - port: {self.port}",
            f"      targetPort: {self.port}",
        ]).strip() + "\n"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "service": self.service,
            "image": self.image,
            "port": self.port,
            "replicas": self.replicas,
            "env": dict(self.env),
        }


class DeployProfileBuilder:
    VERSION = "1.0"

    def build_default(self, service: str = "backend") -> DeployProfile:
        return DeployProfile(
            service=service,
            image=f"{service}:latest",
            env={
                "ENV": "production",
                "DASHSCOPE_API_KEY": "${DASHSCOPE_API_KEY}",
            },
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["DeployProfile", "DeployProfileBuilder"]
