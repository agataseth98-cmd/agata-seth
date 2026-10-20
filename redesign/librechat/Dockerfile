ARG LIBRECHAT_BASE=ghcr.io/danny-avila/librechat@sha256:b07248d86e020c44101170bde2dbb4ab547df30dd223b4aacd6218cc90e8632b
FROM ${LIBRECHAT_BASE} AS patched

USER root
RUN apk add --no-cache git
COPY fork/agata-capabilities.patch /tmp/agata-capabilities.patch
RUN git -C /app apply --check /tmp/agata-capabilities.patch \
    && git -C /app apply /tmp/agata-capabilities.patch

FROM ${LIBRECHAT_BASE}
COPY --from=patched /app/api/server/services/MCP.js /app/api/server/services/MCP.js
COPY --from=patched /app/api/server/services/agataCapabilities.js /app/api/server/services/agataCapabilities.js
COPY --from=patched /app/api/server/controllers/agents/resume.js /app/api/server/controllers/agents/resume.js
