pipeline {
    agent none

    stages {
        stage('Checkout SCM') {
            agent { label 'node1' }
            steps {
                script {
                    checkout scm
                }
            }
        }

        stage('Build & Deploy') {
            agent { label 'node1' }
            steps {
                script {
                    sh """
                        set -e

                        BRANCH_NAME="${env.BRANCH_NAME}"
                        echo \"🌿 Current branch: \$BRANCH_NAME\"

                        echo \"📦 Cloning repo if not present\"
                        git clone git@github.com:magicchat-core/serverless_infra.git || true

                        echo \"🐍 Creating virtual environment (if not exists)\"
                        python3 -m venv ~/artifactory_py_packages/cloud_utils/artificator_env || true

                        echo \"🔧 Activating virtual environment\"
                        . ~/artifactory_py_packages/cloud_utils/artificator_env/bin/activate

                        echo \"🔁 Reinstalling private repo in editable mode\"
                        rm -rf ~/serverless_infra
                        git clone git@github.com:magicchat-core/serverless_infra.git ~/serverless_infra

                        echo \"📥 Installing in editable mode\"
                        pip install -e ~/serverless_infra

                        echo \"🛠  Setting PYTHONPATH\"
                        export PYTHONPATH=~/serverless_infra:\$PYTHONPATH

                        echo \"🔎 Checking import\"
                        python -c "import cloud_utils; print('✅ cloud_utils import successful')"

                        echo \"✅ Cloud utils package imported successfully.\"

                        # Run update_stacks.py only if branch is dev or master
                        if [ \"\$BRANCH_NAME\" = \"dev\" ]; then
                            echo \"🚀 Running update_stacks.py for dev branch\"
                            ~/artifactory_py_packages/cloud_utils/artificator_env/bin/python3 update_stacks.py dev
                        elif [ \"\$BRANCH_NAME\" = \"master\" ]; then
                            echo \"🚀 Running update_stacks.py for master branch\"
                            ~/artifactory_py_packages/cloud_utils/artificator_env/bin/python3 update_stacks.py prod
                        else
                            echo \"⚠️ Skipping stack update. Current branch: \$BRANCH_NAME\"
                        fi
                    """


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
