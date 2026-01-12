#!/bin/bash

# Backend EKS 배포 스크립트
set -e

# 설정
AWS_REGION="ap-northeast-2"
AWS_ACCOUNT_ID="324547056370"
ECR_REPOSITORY="library-api"  # 내 전용 레포지토리
EKS_CLUSTER_NAME="one"
IMAGE_TAG="latest"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Backend EKS 배포 시작 ===${NC}"

# 1. AWS CLI 및 Docker 확인
echo -e "${YELLOW}1. 환경 확인...${NC}"
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI가 설치되지 않았습니다${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker가 설치되지 않았습니다${NC}"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl이 설치되지 않았습니다${NC}"
    exit 1
fi

# 2. ECR 레포지토리 생성 (없으면)
echo -e "${YELLOW}2. ECR 레포지토리 확인/생성...${NC}"
if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null; then
    echo "ECR 레포지토리 생성 중..."
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
else
    echo "ECR 레포지토리 이미 존재함"
fi

# 3. ECR 로그인
echo -e "${YELLOW}3. ECR 로그인...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 4. Docker 이미지 빌드
echo -e "${YELLOW}4. Docker 이미지 빌드...${NC}"
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

# 5. 이미지 태그 및 푸시
echo -e "${YELLOW}5. ECR에 이미지 푸시...${NC}"
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# 6. EKS 클러스터 연결
echo -e "${YELLOW}6. EKS 클러스터 연결...${NC}"
aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME

# 7. Kubernetes 배포
echo -e "${YELLOW}7. Kubernetes에 배포...${NC}"
kubectl apply -f k8s-deployment.yaml

# 8. 배포 상태 확인
echo -e "${YELLOW}8. 배포 상태 확인...${NC}"
kubectl rollout status deployment/library-backend -n default

# 9. Pod 상태 확인
echo -e "${YELLOW}9. Pod 상태 확인...${NC}"
kubectl get pods -l app=library-backend -n default

# 10. 서비스 확인
echo -e "${YELLOW}10. 서비스 확인...${NC}"
kubectl get service library-backend-service -n default

echo -e "${GREEN}=== 배포 완료! ===${NC}"
echo ""
echo "다음 명령어로 상태를 확인할 수 있습니다:"
echo "kubectl get pods -l app=library-backend -n default"
echo "kubectl logs -l app=library-backend -n default"
echo "kubectl describe service library-backend-service -n default"