pipeline {
    agent any
    environment {
        container_name = "c_${BUILD_ID}_${JENKINS_NODE_COOKIE}"
        user_ci = credentials('lsst-io')
        XML_REPORT="jenkinsReport/report.xml"
        work_branches = "${GIT_BRANCH} ${CHANGE_BRANCH} develop"
    }
    stages {
        stage("Pulling image.") {
            steps {
                script {
                    sh """
                    docker pull lsstts/develop-env:develop
                    """
                }
            }
        }
        stage("Start container") {
            steps {
                script {
                    sh """
                    chmod -R a+rw \${WORKSPACE}
                    container=\$(docker run -v \${WORKSPACE}:/home/saluser/repo/ -td --rm --name \${container_name} -e LTD_USERNAME=\${user_ci_USR} -e LTD_PASSWORD=\${user_ci_PSW} lsstts/develop-env:develop)
                    """
                }
            }
        }
        stage("Running tests") {
            steps {
                script {
                    sh """
                    docker exec -u saluser \${container_name} sh -c \"source ~/.setup.sh && cd repo && pip install --ignore-installed -e . && eups declare -r . -t saluser && setup ts_ess_common -t saluser && pytest --junitxml=\${XML_REPORT}\"
                    """
                }
            }
        }
        stage("Trigger the EssController job"){
            steps {
                build job: 'LSST_Telescope-and-Site/ts_ess_controller', wait: false
            }
        }
        stage("Trigger the EssCsc job"){
            steps {
                build job: 'LSST_Telescope-and-Site/ts_ess_csc', wait: false
            }
        }
    }
    post {
        always {
            // Publish the HTML report
            publishHTML (target: [
                allowMissing: false,
                alwaysLinkToLastBuild: false,
                keepAll: true,
                reportDir: 'jenkinsReport/',
                reportFiles: 'index.html',
                reportName: "Coverage Report"
              ])
        }
        cleanup {
            sh """
                docker exec -u root --privileged \${container_name} sh -c \"chmod -R a+rw /home/saluser/repo/ \"
                docker stop \${container_name}
            """
            deleteDir()
        }
    }
}
