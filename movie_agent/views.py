import requests
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from .utils import SSRecommander, GoogleAuthUtils
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect



class MovieAgentViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    ssrecommander = SSRecommander()

    def hello(self, request):
        return Response({"message": "Hello from MCP Agent!"})

    def handle_onboarding_suggestions(self, request):
        user = request.user
        res, status = self.ssrecommander.handle_onboarding_suggestions(
            user, **request.query_params.dict())
        return Response(res, status=status)
    
    def suggestions_by_query(self, request):
        user = request.user
        res, status = self.ssrecommander.suggestions_by_query(
            user, **request.query_params.dict())
        return Response(res, status=status)
    
    def update_usr_cnt_feedback(self, request, id):
        res, status = self.ssrecommander.update_usr_cnt_feedback(
            id, **request.data)
        return Response(res, status=status)


class GoogleAuthViewSet(ViewSet):
    google_auth_utils = GoogleAuthUtils()

    def refresh_google_token(self, request):
        """Refresh Google access token manually."""
        user = request.user
        access_token, ok = self.google_auth_utils.refresh_user_google_token(user)
        if not ok:
            return Response({"code": 400, "message": "Failed to refresh token"}, status=200)
        return Response({"code": 0, "access_token": access_token}, status=200)

    def start(self, request):
        """Step 1: Return Google OAuth URL"""
        auth_url, state = self.google_auth_utils.generate_auth_url()
        request.session["google_oauth_state"] = state
        return Response({"auth_url": auth_url})
    
    def exchange(self, request):
        """Step 2: Exchange auth code for tokens & save in DB"""
        code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri")

        if not code:
            return Response({"code": 400, "message": "Missing code"}, status=200)

        try:
            res, status = self.google_auth_utils.exchange_code_for_tokens(code, redirect_uri)
            return Response(res, status=status)
        except Exception as e:
            return Response({"code": 400, "message": str(e)}, 200)
        
    def google_callback(self, request):
        code = request.GET.get("code")
        if not code:
            return Response({"code":400, "message": "Missing code"}, status=200)
        try:
            response = requests.post(
                "https://ss-api-ajuf.onrender.com/google/exchange",
                json={"code": code, "redirect_uri": "https://ss-api-ajuf.onrender.com/ssplanner/oauth2callback/"},
                cookies=request.COOKIES,
            )

            data = response.json()

            if response.status_code == 200 and data.get("data"):
                access_token = data["data"]["access_token"]
                refresh_token = data["data"]["refresh_token"]
                print(refresh_token)
                # Redirect user to React app with tokens
                return redirect(f"https://sspui.netlify.app/movies?auth=success&access={access_token}&refresh={refresh_token}")

            return Response({"code":400, "message": "Token exchange failed"}, status=200)

        except Exception as e:
            return Response({"code":400, "message": str(e)}, status=200)
            
    