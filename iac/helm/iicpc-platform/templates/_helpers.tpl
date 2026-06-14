{{/*
Helm template helpers for IICPC Platform
Common functions and definitions used across all templates
*/}}

{{/*
Define application labels
*/}}
{{- define "iicpc.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Define selector labels
*/}}
{{- define "iicpc.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Define service account name
*/}}
{{- define "iicpc.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- .Values.serviceAccount.name | default (printf "%s-sa" (include "iicpc.name" .)) -}}
{{- else -}}
{{- .Values.serviceAccount.name | default "default" -}}
{{- end -}}
{{- end -}}

{{/*
Define image pull secrets
*/}}
{{- define "iicpc.imagePullSecrets" -}}
{{- if .Values.imagePullSecrets }}
{{- range .Values.imagePullSecrets }}
- name: {{ . }}
{{- end }}
{{- end }}
{{- if and .Values.global .Values.global.imagePullSecrets }}
{{- range .Values.global.imagePullSecrets }}
- name: {{ . }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Define resource requirements
*/}}
{{- define "iicpc.resources" -}}
{{- if .Values.resources }}
limits:
  cpu: {{ .Values.resources.limits.cpu }}
  memory: {{ .Values.resources.limits.memory }}
requests:
  cpu: {{ .Values.resources.requests.cpu }}
  memory: {{ .Values.resources.requests.memory }}
{{- end }}
{{- end -}}

{{/*
Define autoscaling
*/}}
{{- define "iicpc.autoscaling" -}}
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "iicpc.fullname" . }}-hpa
  labels:
    {{- include "iicpc.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "iicpc.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
{{- end }}
{{- end -}}

{{/*
Define pod affinity
*/}}
{{- define "iicpc.affinity" -}}
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: workload
              operator: In
              values: ["general", "botfleet", "federation"]
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values: ["hosting", "evaluation", "federation", "governance", "strategic"]
          topologyKey: kubernetes.io/hostname
{{- end -}}

{{/*
Define ingress annotations
*/}}
{{- define "iicpc.ingressAnnotations" -}}
nginx.ingress.kubernetes.io/rate-limit: "100"
nginx.ingress.kubernetes.io/rate-limit-window: "1m"
nginx.ingress.kubernetes.io/rate-limit-burst: "10"
nginx.ingress.kubernetes.io/proxy-body-size: "10m"
nginx.ingress.kubernetes.io/proxy-read-timeout: "60s"
nginx.ingress.kubernetes.io/proxy-send-timeout: "60s"
{{- end -}}

{{/*
Define TLS secret
*/}}
{{- define "iicpc.tlsSecret" -}}
{{- $fullName := include "iicpc.fullname" . }}
{{- $tls := .Values.tls }}
{{- if $tls }}
apiVersion: v1
kind: Secret
type: kubernetes.io/tls
metadata:
  name: {{ $fullName }}-tls
  labels:
    {{- include "iicpc.labels" $ | nindent 4 }}
spec:
  domains:
    {{- range $tls.hosts }}
    - {{ . }}
    {{- end }}
  {{- if $tls.cert }}
  data:
    tls.crt: {{ $tls.cert | b64enc }}
    tls.key: {{ $tls.key | b64enc }}
  {{- end }}
{{- end }}
{{- end -}}



{{/*
Generate app name
*/}}
{{- define "iicpc.name" -}}
{{- if .Values.nameOverride -}}
{{- .Values.nameOverride -}}
{{- else if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride -}}
{{- else -}}
{{- .Chart.Name -}}
{{- end -}}
{{- end -}}

{{/*
Generate fullname
*/}}
{{- define "iicpc.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride -}}
{{- else -}}
{{- $name := .Chart.Name -}}
{{- if .Values.suffix -}}
{{- printf "%s-%s" $name .Values.suffix -}}
{{- else -}}
{{- printf "%s" $name -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Generate chart version
*/}}
{{- define "iicpc.chartVersion" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/*
Check if external service is enabled
*/}}
{{- define "iicpc.isExternalServiceEnabled" -}}
{{- if hasKey .Values.global "postgresql" }}{{ .Values.global.postgresql.enabled }}{{ else }}false{{- end }}
{{- end -}}

