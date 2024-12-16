from rest_framework.views import APIView
from .serializers import (
    RegisterSerializer,
    EmailVerifyBeginSerializer,
    EmailVerifyCompleteSerializer,
    TOTPDeviceCreateSerializer,
    QRCodeDataSerializer,
    VerifyTOTPDeviceSerializer,
)
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
import qrcode
from io import BytesIO
from rest_framework.renderers import BaseRenderer, BrowsableAPIRenderer


class RegisterView(APIView):
    serializer_class = RegisterSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(operation_id="v1_register", tags=["auth_v1"])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            new_user_data = serializer.save()
            response_data = self.serializer_class(new_user_data).data
            return Response({"data": response_data}, status=status.HTTP_201_CREATED)


class VerifyEmailBeginView(APIView):
    """
    This view exists to initialize email verification manually if the auto option fails.
    """

    serializer_class = EmailVerifyBeginSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(operation_id="v1_verify_email_begin", tags=["auth_v1"])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_data = serializer.save()
            response_data = self.serializer_class(user_data).data
            return Response({"data": response_data}, status=status.HTTP_200_OK)


class VerifyEmailCompleteView(APIView):
    serializer_class = EmailVerifyCompleteSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(operation_id="v1_verify_email_complete", tags=["auth_v1"])
    def post(self, request, token):
        serializer = self.serializer_class(data={}, context={"token": token})
        if serializer.is_valid(raise_exception=True):
            user_data = serializer.save()
            response_data = self.serializer_class(user_data).data
            return Response({"data": response_data}, status=status.HTTP_200_OK)


class TOTPDeviceCreateView(APIView):
    serializer_class = TOTPDeviceCreateSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(operation_id="v1_create_totp_device", tags=["auth_v1"])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            device_data = serializer.save()
            response_data = self.serializer_class(device_data).data
            return Response({"data": response_data}, status=status.HTTP_201_CREATED)


class GetQRCodeView(APIView):
    serializer_class = QRCodeDataSerializer
    throttle_classes = [AnonRateThrottle]

    class PNGRenderer(BaseRenderer):
        media_type = "image/png"
        format = "png"
        charset = None
        render_style = "binary"

        def render(self, data, accepted_media_type=None, renderer_context=None):
            return data

    @extend_schema(operation_id="v1_get_qrcode", tags=["auth_v1"])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            otpauth_url = serializer.save()
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(otpauth_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color=(0, 0, 0), back_color=(255, 255, 255))
            image_buffer = BytesIO()
            img.save(image_buffer)
            image_buffer.seek(0)
            return Response(
                image_buffer.getvalue(),
                content_type="image/png",
                status=status.HTTP_200_OK,
            )

    def finalize_response(self, request, response, *args, **kwargs):
        """
        This method defines renderers for both image and text.
        PNGRenderer is used when the response contains the QR code.
        BrowsableAPIRenderer is in case of error messages, compatible with DRF's browsable API.
        """
        if response.content_type == "image/png":
            response.accepted_renderer = GetQRCodeView.PNGRenderer()
            response.accepted_media_type = GetQRCodeView.PNGRenderer.media_type
            response.renderer_context = {}
        else:
            response.accepted_renderer = BrowsableAPIRenderer()
            response.accepted_media_type = BrowsableAPIRenderer.media_type
            response.renderer_context = {
                "response": response.data,
                "view": self,
                "request": request,
            }
        for key, value in self.headers.items():
            response[key] = value
        return response


class VerifyTOTPDeviceView(APIView):
    serializer_class = VerifyTOTPDeviceSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(operation_id="v1_verify_totp_device", tags=["auth_v1"])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            device_data = serializer.save()
            response_data = self.serializer_class(device_data).data
            return Response({"data": response_data}, status=status.HTTP_200_OK)