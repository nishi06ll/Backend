from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegister
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.authtoken.models import Token
from .serializers import MovieSerializer
from django.shortcuts import get_object_or_404
from .permission import IsAdminUserOrReadOnly
from datetime import datetime
from django.http import JsonResponse
from .serializers import BookingSerializer
import logging
import razorpay 
from django.conf import settings
from .models import Movie, Booking
from xhtml2pdf import pisa
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from django.core.files.base import ContentFile
from django.core.mail import send_mail
import io 
from io import BytesIO
logger = logging.getLogger(__name__)
import qrcode


@api_view(['POST'])
@permission_classes([AllowAny,])
def signup(request):
    if request.method == 'POST':
        serializer = UserRegister(data=request.data)
        if serializer.is_valid():
            account = serializer.save()
            return Response({
                'response': 'registered',
                'username': account.username,
                'email': account.email,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},
                        status=HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid Credentials'},
                        status=HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key},status=HTTP_200_OK)

@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def logout(request):
    token_key = request.auth

    if token_key:
        token_key.delete()
        return Response({ 'succesfull logout'}, status=200)
    return Response({'error':'eorro'},status=400)

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def list(request):
    movie = Movie.objects.filter()
    serializer = MovieSerializer(movie, many=True)
    return Response(serializer.data)
    

# @api_view(['POST'])
# @permission_classes((IsAdminUserOrReadOnly,))
# def create(request):
#     serializer = MovieSerializer(data=request.data)
#     if serializer.is_valid():
#         instance = serializer.save()
#         return Response({'id': instance.id}, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['PUT'])
# @permission_classes((IsAdminUserOrReadOnly,))
# def change(request, pk):
#     movie = get_object_or_404(Movie, pk=pk)
#     serializer = MovieSerializer(request.data, instance=movie)
#     if serializer.is_valid():
#         serializer.save()
#         serializer = MovieSerializer(Movie)
#         return Response(serializer.data)
#     else:
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# @api_view(['DELETE'])
# @permission_classes((IsAdminUserOrReadOnly,))
# def delete(request, pk):
#     try:
#         movie = Movie.objects.get(pk=pk)
#     except Movie.DoesNotExist:
#         return Response(status=status.HTTP_404_NOT_FOUND)

#     movie.delete()
#     return Response("deleted successfully")

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def view(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if not movie.is_active:
        return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = MovieSerializer(movie)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes((IsAuthenticated))
def shows(request, date):
    try:
        date = datetime.strptime(date, '%Y-%m-%d')
        shows = Movie.objects.filter(date=date)
        serializer = MovieSerializer(shows, many=True)
        return JsonResponse(serializer.data, safe=False)
    except ValueError:
     return JsonResponse({'error': 'Invalid date format. Please use YYYY-MM-DD.'}, status=400)

@api_view(["POST"])
@permission_classes((AllowAny,))
def admin(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},
                        status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user or not user.is_staff:
        return Response({'error': 'Invalid Credentials'},
                        status=HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key}, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes((AllowAny,))
def disable(request, pk):
    try:
        movie = Movie.objects.get(pk=pk)
    except Movie.DoesNotExist:
        return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)
    movie.is_active = False
    movie.save()
    serializer = MovieSerializer(movie)
    return Response(serializer.data)



def create_razorpay_order(amount_in_cents):
    client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_SECRET_KEY))
    order = client.order.create(
        {"amount": amount_in_cents, "currency": "INR", "payment_capture": "1"}
    )
    return order

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1, 
        error_correction=qrcode.constants.ERROR_CORRECT_M, 
        box_size=10,  
        border=4,  
    )
    qr.add_data(data)  
    qr.make(fit=True)  
    img = qr.make_image(fill_color="black", back_color="white")
    return img


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_payment(request, pk):

    tickets = request.data.get('tickets',1)
    date = request.data.get('date','2024-01,01')
    try:
        movie = Movie.objects.get(pk=pk, is_active=True)
    except Movie.DoesNotExist:
        return JsonResponse({'error': 'Movie Dose not match'},status=404)
    if tickets <= 0:
        return JsonResponse({'error': 'Invalid Ticket Counts'},status=404)
    total_cost = movie.ticket_amount * tickets

    razorpay_order = create_razorpay_order(int(total_cost * 100))
    booking = Booking(
        user = request.user,
        movie = movie,
        tickets = tickets,
        booking_date = datetime.now(),
        razorpay_order_id = razorpay_order['id'],
        date = date,
    )

    booking.save()

    return JsonResponse({"message": "Razorpay order created","razorpay_order_id": razorpay_order['id'], "amount": total_cost}, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_payment_success(request):
    try:
        data = request.data
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")

        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_SECRET_KEY))
        payment_details = client.payment.fetch(razorpay_payment_id)

        if payment_details["status"] != "captured":
            return Response({"error": "Payment not captured"}, status=400)

        booking = Booking.objects.get(razorpay_order_id=razorpay_order_id)
        qr_data = f"Booking ID: {booking.id}, Movie: {booking.movie.name}, User: {booking.user.username}, Email: {booking.user.email}"

        qr_code = generate_qr_code(qr_data)

        qr_io = io.BytesIO()
        qr_code.save(qr_io, format="PNG")
        qr_io.seek(0)

        qr_filename = f"booking_{booking.id}_qr.png"
        booking.qr_image.save(qr_filename, ContentFile(qr_io.read()), save=True)

        send_mail(
        subject="Your Booking Confirmation",
        message=f"Your booking with ID {booking.id} is confirmed.your show name {booking.movie.name} enjoy your show {booking.user.username}.{booking.qr_image}",
        from_email="no-reply@theatre.com",
        recipient_list=[booking.user.email],
        fail_silently=False,
    )


        return Response({"message": "Booking confirmed", "booking_id": booking.id}, status=200)
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")
        return Response({"error": "Internal Server Error"}, status=500)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings_api(request):
    bookings = Booking.objects.filter(user=request.user).order_by("-booking_date")
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_pdf(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    base_url = request.build_absolute_uri('/')

    qr_image_url = base_url + booking.qr_image.url[1:]
    print(qr_image_url) 

    context = {
        'booking': {
            'movie': booking.movie,
            'user': booking.user,
            'id': booking.id,
            'booking_date': booking.booking_date,
            'tickets': booking.tickets,
            'razorpay_order_id': booking.razorpay_order_id,
            'qr_image': {
                'url': qr_image_url
            }
        }
    }

    template = get_template('booking_pdf.html')
    html = template.render(context)

    buffer = BytesIO()

    pisa_status = pisa.CreatePDF(html, dest=buffer)

    if pisa_status.err:
        return Response({"error": "PDF creation error!"}, status=500)
    else:
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{booking.id}.pdf"'
        return response


