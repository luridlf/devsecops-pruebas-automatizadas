// Pipeline DevSecOps - OCY1102 Ciberseguridad en desarrollo (Guía 3.2.2)
// Jenkins corre en Docker y usa el daemon del host (docker.sock) para construir,
// probar y desplegar la app, y para ejecutar OWASP ZAP.
// ZAP_IMAGE, ZAP_TARGET_URL y DOCKER_NETWORK son variables globales definidas en Jenkins.
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        APP_IMAGE     = 'vulnerable-flask-app'
        APP_CONTAINER = 'vulnerable-app'
        APP_PORT      = '5000'
    }

    stages {
        stage('Build') {
            steps {
                echo 'Construyendo la imagen Docker de la aplicación Flask...'
                sh 'docker build -t ${APP_IMAGE}:${BUILD_NUMBER} -t ${APP_IMAGE}:latest .'
            }
        }

        stage('Test') {
            steps {
                echo 'Ejecutando pruebas unitarias con pytest dentro de la imagen...'
                sh '''
                    docker rm -f test-${BUILD_NUMBER} 2>/dev/null || true
                    docker run --name test-${BUILD_NUMBER} ${APP_IMAGE}:${BUILD_NUMBER} \
                        python -m pytest -v --junitxml=test-results.xml --cov=app --cov-report=xml:coverage.xml
                    docker cp test-${BUILD_NUMBER}:/app/test-results.xml .
                    docker cp test-${BUILD_NUMBER}:/app/coverage.xml .
                    # coverage.xml trae la ruta del contenedor (/app); se ajusta al workspace para SonarQube
                    sed -i "s#<source>/app</source>#<source>${WORKSPACE}</source>#" coverage.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                    sh 'docker rm -f test-${BUILD_NUMBER} 2>/dev/null || true'
                }
            }
        }

        stage('Analyze') {
            steps {
                echo 'Análisis estático de calidad y seguridad (SAST) con SonarQube...'
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectVersion=${BUILD_NUMBER}"
                    }
                }
                timeout(time: 5, unit: 'MINUTES') {
                    // No aborta: el objetivo es reportar hallazgos, no bloquear la demo
                    waitForQualityGate abortPipeline: false
                }
            }
        }

        stage('Deploy') {
            steps {
                echo 'Desplegando la app en el entorno de prueba (red Docker accesible para ZAP)...'
                sh '''
                    docker rm -f ${APP_CONTAINER} 2>/dev/null || true
                    docker run -d --name ${APP_CONTAINER} --network ${DOCKER_NETWORK} \
                        -p ${APP_PORT}:5000 ${APP_IMAGE}:${BUILD_NUMBER}
                    for i in $(seq 1 30); do
                        curl -fs "http://${APP_CONTAINER}:5000/hello?name=TEST" && exit 0
                        sleep 2
                    done
                    echo "La aplicación no respondió a tiempo" && exit 1
                '''
            }
        }

        stage('Security Test') {
            parallel {
                stage('OWASP Dependency-Check') {
                    steps {
                        echo 'Análisis de composición de software (SCA) sobre requirements.txt...'
                        catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                            withCredentials([string(credentialsId: 'nvd-api-key', variable: 'NVD_API_KEY')]) {
                                dependencyCheck odcInstallation: 'DependencyCheck',
                                    additionalArguments: '''
                                        --project "devsecops-pruebas-automatizadas"
                                        --scan requirements.txt
                                        --enableExperimental
                                        --format HTML --format XML --format JSON
                                        --data /var/dependency-check-data
                                        --nvdApiKey ${NVD_API_KEY}
                                    '''
                            }
                        }
                    }
                    post {
                        always {
                            dependencyCheckPublisher pattern: 'dependency-check-report.xml'
                        }
                    }
                }

                stage('OWASP ZAP') {
                    steps {
                        echo "Análisis dinámico (DAST) con OWASP ZAP sobre ${ZAP_TARGET_URL}..."
                        sh '''
                            docker rm -f zap-${BUILD_NUMBER} 2>/dev/null || true
                            docker run --name zap-${BUILD_NUMBER} --network ${DOCKER_NETWORK} ${ZAP_IMAGE} \
                                bash -c "mkdir -p /zap/wrk && zap-full-scan.py -t '${ZAP_TARGET_URL}' \
                                    -r zap-report.html -J zap-report.json -w zap-report.md -m 1 -I"
                            docker cp zap-${BUILD_NUMBER}:/zap/wrk/zap-report.html .
                            docker cp zap-${BUILD_NUMBER}:/zap/wrk/zap-report.json .
                            docker cp zap-${BUILD_NUMBER}:/zap/wrk/zap-report.md .
                        '''
                    }
                    post {
                        always {
                            sh 'docker rm -f zap-${BUILD_NUMBER} 2>/dev/null || true'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts allowEmptyArchive: true,
                artifacts: 'zap-report.*, dependency-check-report.*, test-results.xml, coverage.xml'
            publishHTML(target: [reportName: 'OWASP ZAP', reportDir: '.', reportFiles: 'zap-report.html',
                                 keepAll: true, alwaysLinkToLastBuild: true, allowMissing: true])
            publishHTML(target: [reportName: 'Dependency-Check', reportDir: '.', reportFiles: 'dependency-check-report.html',
                                 keepAll: true, alwaysLinkToLastBuild: true, allowMissing: true])
        }
        success {
            echo "Pipeline OK. App de prueba disponible en http://localhost:${APP_PORT}/hello?name=TEST"
        }
    }
}
