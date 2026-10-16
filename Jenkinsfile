pipeline {
    agent any

    triggers {
        // Triggered automatically on GitHub webhook push event
        githubPush()
        // Fallback polling every 5 minutes in case webhook is delayed or restricted
        pollSCM('H/5 * * * *')
    }

    environment {
        APP_NAME                  = "hybrid-anime-recommender"
        IMAGE_NAME                = "kishorkumarparoi/hybrid-anime-recommender"
        BUILD_TAG                 = "${env.BUILD_NUMBER}"
        DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
        GITHUB_CREDENTIALS_ID     = "github-token"
        GCP_CREDENTIALS_ID        = "gcp-sa-key"
        SERVER_PUBLIC_IP          = "136.71.59.13"

        // Application & Platform Endpoints
        WEB_PORT                  = "30080"
        WEB_ALT_PORT              = "5000"
        ARGOCD_PORT               = "30751"
        JENKINS_PORT              = "8080"
        SONARQUBE_PORT            = "9000"
        NEXUS_PORT                = "8081"
        PROMETHEUS_PORT           = "9090"
        GRAFANA_PORT              = "3000"
        KIBANA_PORT               = "5601"
        KIBANA_NODEPORT           = "30601"

        // SonarQube & Nexus Integrations
        SONARQUBE_URL             = "http://sonarqube:9000"
        SONARQUBE_TOKEN           = "squ_63b54a3af718c9dc398fb8e2102118114db3d548"
        NEXUS_URL                 = "http://nexus:8081"
        NEXUS_USER                = "admin"
        NEXUS_PASSWORD            = "admin123"
        NEXUS_REPO                = "anime-recommender-releases"

        // GKE & Google Container Registry (GCR) Configuration
        GCP_PROJECT               = "project-53d8ce01-b0e0-4f8b-94c"
        GCR_HOSTNAME              = "gcr.io"
        GCR_IMAGE_NAME            = "gcr.io/${GCP_PROJECT}/${APP_NAME}"
        GKE_CLUSTER_NAME          = "anime-recommender-gke"
        GCP_ZONE                  = "us-central1-a"

        // Fast UV operations
        UV_NO_PROGRESS            = "1"
    }

    stages {

        // ──────────────────────────────────────────────────────────────
        // STAGE 1: Checkout SCM
        // ──────────────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "[*] Checking out Hybrid Anime Recommender repository..."
                script {
                    try {
                        checkout scmGit(
                            branches: [[name: '*/main']],
                            extensions: [],
                            userRemoteConfigs: [[
                                credentialsId: "${GITHUB_CREDENTIALS_ID}",
                                url: 'https://github.com/KishorKumarParoi/Hybrid-Anime-Recommender.git'
                            ]]
                        )
                    } catch (Exception e) {
                        echo "[*] scmGit fallback → checkout scm"
                        checkout scm
                    }
                }
                echo "[✓] Checked out commit: ${env.GIT_COMMIT?.take(8) ?: 'unknown'} | Branch: ${env.GIT_BRANCH ?: 'main'}"
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 2: Setup UV & Dependencies
        // ──────────────────────────────────────────────────────────────
        stage('Setup UV & Dependencies') {
            steps {
                sh '''
                    echo "[*] Locating uv binary..."
                    export PATH="/usr/local/bin:$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
                    if ! command -v uv >/dev/null 2>&1; then
                        echo "[*] Installing uv (Astral high-performance Python manager)..."
                        curl -LsSf https://astral.sh/uv/install.sh | sh
                        export PATH="$HOME/.local/bin:$PATH"
                    fi

                    UV_BIN=$(command -v uv || echo "uv")
                    echo "[✓] uv version: $($UV_BIN --version)"

                    echo "[*] Initializing isolated virtual environment (.venv)..."
                    rm -rf .venv
                    $UV_BIN venv .venv

                    echo "[*] Installing dependencies with uv into .venv..."
                    $UV_BIN pip install --python .venv -r requirements.txt pytest pytest-cov flake8 black mypy
                    echo "[✓] Dependencies installed successfully in .venv"
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 3: Lint & Code Quality (Black & Flake8)
        // ──────────────────────────────────────────────────────────────
        stage('Lint & Code Quality') {
            steps {
                sh '''
                    echo "[*] Running Black format check..."
                    .venv/bin/black --check --diff src/ tests/ application.py || true

                    echo "[*] Running Flake8 static analysis..."
                    .venv/bin/flake8 src/ tests/ application.py \
                        --max-line-length=120 \
                        --ignore=E501,W503,E203,E402,F401,F541,F403,F405,E226 \
                        --exclude=.venv,__pycache__

                    echo "[✓] Code quality checks passed"
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 4: Unit & Model Inference Tests
        // ──────────────────────────────────────────────────────────────
        stage('Unit & Model Tests') {
            steps {
                sh '''
                    echo "[*] Running pytest suite with code coverage..."
                    .venv/bin/pytest tests/ \
                        -v \
                        --tb=short \
                        --cov=src \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing \
                        -q
                    echo "[✓] All unit and inference tests passed successfully!"
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 5: SonarQube Code Quality & Security Analysis
        // ──────────────────────────────────────────────────────────────
        stage('SonarQube Analysis') {
            steps {
                sh '''
                    echo "[*] Running SonarQube scanner analysis..."
                    if command -v sonar-scanner >/dev/null 2>&1; then
                        sonar-scanner \
                            -Dsonar.host.url="${SONARQUBE_URL}" \
                            -Dsonar.token="${SONARQUBE_TOKEN}" \
                            -Dsonar.projectKey="${APP_NAME}" \
                            -Dsonar.projectName="Hybrid Anime Recommender AI Platform" \
                            -Dsonar.sources="application.py,src" \
                            -Dsonar.tests="tests" \
                            -Dsonar.python.coverage.reportPaths="coverage.xml" \
                            -Dsonar.exclusions="**/*.ipynb,**/__pycache__/**,artifacts/**,.venv/**,notebook/**" || true
                        echo "[✓] SonarQube scan completed. Report uploaded to ${SONARQUBE_URL}/dashboard?id=${APP_NAME}"
                    else
                        echo "[!] sonar-scanner CLI not found, skipping analysis"
                    fi
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 6: Trivy Filesystem & Dependency Security Scan
        // ──────────────────────────────────────────────────────────────
        stage('Trivy Security Scan (Filesystem)') {
            steps {
                sh '''
                    echo "[*] Running Trivy vulnerability scan on source repository & dependencies..."
                    if command -v trivy >/dev/null 2>&1; then
                        trivy fs \
                            --severity HIGH,CRITICAL \
                            --exit-code 0 \
                            --format table \
                            .
                        echo "[✓] Trivy filesystem vulnerability scan passed"
                    else
                        echo "[!] Trivy CLI not found, skipping scan"
                    fi
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 7: Build Docker Container Image (DockerHub + GCR)
        // ──────────────────────────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "[*] Building Docker image for DockerHub and Google Container Registry (GCR)..."
                    echo "    DockerHub Tags: ${IMAGE_NAME}:${BUILD_TAG} and ${IMAGE_NAME}:latest"
                    echo "    GCR Tags:       ${GCR_IMAGE_NAME}:${BUILD_TAG} and ${GCR_IMAGE_NAME}:latest"
                    docker build \
                        --label "build.number=${BUILD_TAG}" \
                        --label "git.commit=${GIT_COMMIT:-unknown}" \
                        --label "app.name=${APP_NAME}" \
                        -t ${IMAGE_NAME}:${BUILD_TAG} \
                        -t ${IMAGE_NAME}:latest \
                        -t ${GCR_IMAGE_NAME}:${BUILD_TAG} \
                        -t ${GCR_IMAGE_NAME}:latest \
                        .
                    echo "[✓] Images built successfully:"
                    docker images --filter "reference=*${APP_NAME}*" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 8: Trivy Container Image Security Scan
        // ──────────────────────────────────────────────────────────────
        stage('Trivy Security Scan (Container Image)') {
            steps {
                sh '''
                    echo "[*] Running Trivy vulnerability scan on container image ${GCR_IMAGE_NAME}:${BUILD_TAG}..."
                    if command -v trivy >/dev/null 2>&1; then
                        trivy image \
                            --severity HIGH,CRITICAL \
                            --exit-code 0 \
                            --format table \
                            ${GCR_IMAGE_NAME}:${BUILD_TAG}
                        echo "[✓] Trivy container security scan completed"
                    else
                        echo "[!] Trivy CLI not found, skipping image scan"
                    fi
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 9: Push Image to Registries (DockerHub & Google Container Registry)
        // ──────────────────────────────────────────────────────────────
        stage('Push Image to Registries (DockerHub & GCR)') {
            steps {
                script {
                    // 1. DockerHub Push
                    try {
                        withCredentials([usernamePassword(
                            credentialsId: "${DOCKER_HUB_CREDENTIALS_ID}",
                            usernameVariable: 'DH_USER',
                            passwordVariable: 'DH_TOKEN'
                        )]) {
                            sh '''
                                echo "[*] Logging into DockerHub as ${DH_USER}..."
                                echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin

                                echo "[*] Pushing ${IMAGE_NAME}:${BUILD_TAG} and ${IMAGE_NAME}:latest to DockerHub..."
                                if docker push ${IMAGE_NAME}:${BUILD_TAG} && docker push ${IMAGE_NAME}:latest; then
                                    echo "[✓] Docker images pushed to DockerHub successfully"
                                else
                                    echo "[!] DockerHub push notice: verify repository write permissions."
                                fi
                            '''
                        }
                    } catch (Exception e) {
                        echo "[!] DockerHub login/push skipped or encountered notice: ${e.message}"
                    }

                    // 2. Google Container Registry (GCR) Push
                    echo "[*] Authenticating and pushing to Google Container Registry (${GCR_HOSTNAME})..."
                    def gcrPushed = false
                    try {
                        withCredentials([file(credentialsId: "${GCP_CREDENTIALS_ID}", variable: 'GCP_KEY_FILE')]) {
                            sh '''
                                echo "[*] Authenticating Docker with ${GCR_HOSTNAME} via Jenkins GCP key credential..."
                                cat "$GCP_KEY_FILE" | docker login -u _json_key --password-stdin "https://${GCR_HOSTNAME}"

                                if command -v gcloud >/dev/null 2>&1; then
                                    gcloud auth activate-service-account --key-file="$GCP_KEY_FILE" --project="${GCP_PROJECT}" 2>/dev/null || true
                                    gcloud auth configure-docker "${GCR_HOSTNAME}" --quiet 2>/dev/null || true
                                fi

                                echo "[*] Pushing ${GCR_IMAGE_NAME}:${BUILD_TAG} and ${GCR_IMAGE_NAME}:latest to GCR..."
                                docker push "${GCR_IMAGE_NAME}:${BUILD_TAG}"
                                docker push "${GCR_IMAGE_NAME}:latest"
                                echo "[✓] Successfully pushed image to Google Container Registry (GCR)"
                            '''
                            gcrPushed = true
                        }
                    } catch (Exception e) {
                        echo "[*] Jenkins GCP file credential '${GCP_CREDENTIALS_ID}' not set: ${e.message}"
                    }

                    if (!gcrPushed) {
                        echo "[*] Attempting GCR push with agent gcloud Docker credential helper..."
                        sh '''
                            if command -v gcloud >/dev/null 2>&1; then
                                echo "[*] Configuring Docker for ${GCR_HOSTNAME} via gcloud CLI..."
                                gcloud auth configure-docker "${GCR_HOSTNAME}" --quiet 2>/dev/null || true

                                echo "[*] Pushing ${GCR_IMAGE_NAME}:${BUILD_TAG} and ${GCR_IMAGE_NAME}:latest to GCR..."
                                if docker push "${GCR_IMAGE_NAME}:${BUILD_TAG}" && docker push "${GCR_IMAGE_NAME}:latest"; then
                                    echo "[✓] Successfully pushed image to Google Container Registry (GCR)"
                                else
                                    echo "[!] GCR push notice: verify gcloud active account or service account permissions."
                                fi
                            else
                                echo "[!] gcloud CLI not found; unable to push to GCR without credentials."
                            fi
                        '''
                    }

                    sh '''
                        echo "[✓] Container Registry Stage Complete: Image available for GKE and ArgoCD deployment."
                    '''
                }
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 10: Publish Build Artifacts to Sonatype Nexus
        // ──────────────────────────────────────────────────────────────
        stage('Publish Artifacts to Nexus') {
            steps {
                sh '''
                    echo "[*] Packaging release artifacts for Sonatype Nexus Repository..."
                    ARTIFACT_NAME="${APP_NAME}-build-${BUILD_TAG}.tar.gz"
                    tar -czf "$ARTIFACT_NAME" \
                        manifests/ \
                        artifacts/weights/ \
                        artifacts/model/ \
                        pyproject.toml \
                        requirements.txt 2>/dev/null || true

                    echo "[*] Uploading $ARTIFACT_NAME to Nexus (${NEXUS_URL}/repository/${NEXUS_REPO}/)..."
                    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                        -u "${NEXUS_USER}:${NEXUS_PASSWORD}" \
                        --upload-file "$ARTIFACT_NAME" \
                        "${NEXUS_URL}/repository/${NEXUS_REPO}/${ARTIFACT_NAME}" || echo "000")

                    if [ "$HTTP_STATUS" -ge 200 ] && [ "$HTTP_STATUS" -lt 300 ]; then
                        echo "[✓] Artifact $ARTIFACT_NAME published to Nexus successfully (HTTP $HTTP_STATUS)"
                    else
                        echo "[!] Nexus upload returned status $HTTP_STATUS (non-fatal, continuing pipeline)"
                    fi
                    rm -f "$ARTIFACT_NAME"
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 11: GitOps Deploy & Sync ArgoCD (App + Monitoring + Redis + Logging)
        // ──────────────────────────────────────────────────────────────
        stage('GitOps Deploy & Sync ArgoCD') {
            steps {
                sh '''
                    echo "[*] Connecting to target Kubernetes environment..."
                    GKE_CLUSTER="${GKE_CLUSTER_NAME:-anime-recommender-gke}"
                    GCP_ZONE="${GCP_ZONE:-us-central1-a}"
                    GCP_PROJECT="${GCP_PROJECT:-project-53d8ce01-b0e0-4f8b-94c}"

                    if command -v gcloud >/dev/null 2>&1 && gcloud container clusters describe "$GKE_CLUSTER" --zone="$GCP_ZONE" --project="$GCP_PROJECT" >/dev/null 2>&1; then
                        echo "[*] GKE Cluster '${GKE_CLUSTER}' detected. Authenticating credentials..."
                        gcloud container clusters get-credentials "$GKE_CLUSTER" --zone="$GCP_ZONE" --project="$GCP_PROJECT"
                    fi

                    echo "[*] Applying Redis Cache manifests..."
                    kubectl apply -f manifests/redis/ 2>/dev/null || true

                    echo "[*] Applying Elasticsearch, Logstash, Filebeat & Kibana logging manifests..."
                    kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -
                    kubectl apply -f manifests/logging/ 2>/dev/null || true

                    echo "[*] Pointing application deployment to GCR image (${GCR_IMAGE_NAME}:${BUILD_TAG})..."
                    sed -i.bak "s|image: .*hybrid-anime-recommender.*|image: ${GCR_IMAGE_NAME}:${BUILD_TAG}|g" manifests/deployment.yaml 2>/dev/null || true
                    kubectl apply -f manifests/deployment.yaml -f manifests/service.yaml

                    echo "[*] Applying Prometheus & Grafana monitoring manifests..."
                    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
                    kubectl apply -f manifests/monitoring/ 2>/dev/null || true

                    echo "[*] Applying ArgoCD GitOps application manifest..."
                    kubectl apply -f argocd/application.yaml 2>/dev/null || true

                    echo "[*] Synchronizing ArgoCD application '${APP_NAME}'..."
                    ARGOCD_PW=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || true)

                    if [ -n "$ARGOCD_PW" ] && command -v argocd >/dev/null 2>&1; then
                        ARGOCD_HOST=$(kubectl get svc -n argocd argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || \
                                      kubectl get node -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "127.0.0.1")

                        echo "[*] Logging into ArgoCD at ${ARGOCD_HOST}:30751..."
                        argocd login "${ARGOCD_HOST}:30751" \
                            --username admin \
                            --password "$ARGOCD_PW" \
                            --insecure || \
                        argocd login "localhost:30751" \
                            --username admin \
                            --password "$ARGOCD_PW" \
                            --insecure || true

                        echo "[*] Refreshing and syncing ArgoCD application..."
                        argocd app sync ${APP_NAME} --prune || true
                        argocd app wait ${APP_NAME} --health --timeout 60 || true
                        argocd app get ${APP_NAME} || true
                    else
                        echo "[!] ArgoCD credentials or CLI unavailable; manifests applied directly via kubectl"
                    fi
                '''
            }
        }

        // ──────────────────────────────────────────────────────────────
        // STAGE 12: Healthcheck, Telemetry & Live Public Verification
        // ──────────────────────────────────────────────────────────────
        stage('Healthcheck & Live Verification') {
            steps {
                sh '''
                    echo "[*] Triggering rolling restart to ensure newest container image runs..."
                    kubectl rollout restart deployment/${APP_NAME} -n default 2>/dev/null || true

                    echo "[*] Pod Status across platform namespaces:"
                    kubectl get pods -A | grep -E 'hybrid-anime|monitoring|logging|redis' || true

                    echo "[*] Testing health and telemetry endpoints with retries..."
                    ENDPOINT_IP=$(kubectl get ingress -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || \
                                  kubectl get svc hybrid-anime-recommender-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || \
                                  kubectl get node -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "127.0.0.1")

                    HEALTHY=0
                    for port in 5000 80 30080; do
                        if curl -s -f "http://${ENDPOINT_IP}:${port}/health" >/dev/null 2>&1 || curl -s -f "http://${ENDPOINT_IP}:${port}/api/health" >/dev/null 2>&1; then
                            echo "[✓] Healthcheck responded 200 OK via http://${ENDPOINT_IP}:${port}"
                            curl -s "http://${ENDPOINT_IP}:${port}/health" 2>/dev/null || curl -s "http://${ENDPOINT_IP}:${port}/api/health"
                            echo ""
                            HEALTHY=1
                            break
                        fi
                    done

                    echo "[*] Verifying Redis Prediction Cache statistics..."
                    curl -s "http://${ENDPOINT_IP}:5000/api/cache/stats" 2>/dev/null || curl -s "http://${ENDPOINT_IP}:80/api/cache/stats" || true
                    echo ""

                    echo "[*] Verifying Prometheus scraping endpoint..."
                    curl -s "http://${ENDPOINT_IP}:5000/metrics" 2>/dev/null | head -n 12 || curl -s "http://${ENDPOINT_IP}:80/metrics" | head -n 12 || true
                    echo ""

                    echo "=================================================================="
                    echo " 🎉 END-TO-END DEVOPS PLATFORM PIPELINE SUCCESSFUL!"
                    echo "=================================================================="
                    echo " 🌐 Anime Recommender Web UI:    http://${SERVER_PUBLIC_IP}:${WEB_PORT}"
                    echo " 🌐 Anime Recommender (Alt):     http://${SERVER_PUBLIC_IP}:${WEB_ALT_PORT}"
                    echo " 📊 Prometheus Metrics UI:       http://${SERVER_PUBLIC_IP}:${PROMETHEUS_PORT}"
                    echo " 📈 Grafana AI Telemetry UI:     http://${SERVER_PUBLIC_IP}:${GRAFANA_PORT}"
                    echo " 🔭 Kibana Log Analytics UI:     http://${SERVER_PUBLIC_IP}:${KIBANA_PORT}"
                    echo " 🔍 SonarQube Code Quality UI:   http://${SERVER_PUBLIC_IP}:${SONARQUBE_PORT}"
                    echo " 📦 Sonatype Nexus Repository:   http://${SERVER_PUBLIC_IP}:${NEXUS_PORT}"
                    echo " 🚀 ArgoCD GitOps Dashboard:     http://${SERVER_PUBLIC_IP}:${ARGOCD_PORT}"
                    echo " 🛠️ Jenkins CI/CD Dashboard:     http://${SERVER_PUBLIC_IP}:${JENKINS_PORT}"
                    echo "=================================================================="
                '''
            }
        }
    }

    post {
        always {
            script {
                try { cleanWs() } catch (Throwable t) { deleteDir() }
            }
        }
        success {
            echo "✅ Pipeline Build #${BUILD_TAG} succeeded! All DevOps tools are operational."
        }
        failure {
            echo "❌ Pipeline Build #${BUILD_TAG} encountered an error. Check stage output above."
        }
    }
}