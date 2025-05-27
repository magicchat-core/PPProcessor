pipeline {
    agent none  // This ensures that the pipeline doesn't run on any agent by default

    stages {
        stage('Checkout SCM') {
            agent { label 'node1' }  // Ensures this stage runs on 'node1' (the slave node)
            steps {
                script {
                    checkout scm
                }
            }
        }

        stage('Build & Deploy') {
            agent { label 'node1' }  // Ensures this stage runs on 'node1' (the slave node)
            steps {
                script {
                    // Check if the AWS CLI works by calling its full path
                    sh '/usr/local/bin/aws --version'  // Full path to AWS CLI

                    // Use bash explicitly to activate the virtual environment
                    sh '''
                        # Explicitly use bash to activate the virtual environment
                        bash -c "source ~/artifactory_py_packages/cloud_utils/artificator_env/bin/activate && echo 'Virtual environment activated.'"
                        
                        # Check which Python is being used
                        bash -c "which python3"
                        
                        # Explicitly use the virtual environment's Python interpreter
                        ~/artifactory_py_packages/cloud_utils/artificator_env/bin/python3 -c "import cloud_utils"
                        echo "Cloud utils package imported successfully."

                         # Run update_stacks.py only if branch is dev or master
                        if [ "$BRANCH_NAME" = "dev" ]; then
                            echo "Running update_stacks.py for dev branch"
                            ~/artifactory_py_packages/cloud_utils/artificator_env/bin/python3 update_stacks.py dev
                        elif [ "$BRANCH_NAME" = "master" ]; then
                            echo "Running update_stacks.py for master branch"
                            ~/artifactory_py_packages/cloud_utils/artificator_env/bin/python3 update_stacks.py prod
                        else
                            echo "Skipping stack update. Current branch: $BRANCH_NAME"
                        fi
                        
                    '''
                }
            }
        }
    }


    post {
        success {
            echo "✅ Build and deployment successful!"
        }
        failure {
            echo "❌ Build or deployment failed."
        }
    }
}
