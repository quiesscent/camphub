import random
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from faker import Faker

# Import all necessary models
from users.models import Institution, Campus, UserProfile
from academic.models import Course, CourseEnrollment, StudyGroup, StudyGroupMember
from community.models import Event, EventAttendee, Club, ClubMember
from content.models import Post, Comment, Like, Share, UserInteraction
from messaging.models import DirectMessage, GroupChat, GroupChatMember, GroupMessage, Notification, MessageAttachment

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Populate database with realistic test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--institutions',
            type=int,
            default=3,
            help='Number of institutions to create'
        )
        parser.add_argument(
            '--campuses',
            type=int,
            default=2,
            help='Number of campuses per institution'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users per institution'
        )
        parser.add_argument(
            '--courses',
            type=int,
            default=10,
            help='Number of courses per institution'
        )
        parser.add_argument(
            '--purge',
            action='store_true',
            help='Purge existing data before populating'
        )

    def handle(self, *args, **options):
        if options['purge']:
            self.purge_data()
            
        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        # Create institutions and campuses
        institutions = self.create_institutions(options['institutions'], options['campuses'])
        
        # Create users for each institution
        all_users = []
        faculty_users = []
        for institution in institutions:
            users, faculty = self.create_users(institution, options['users'])
            all_users.extend(users)
            faculty_users.extend(faculty)
            
        # Create courses for each institution
        all_courses = []
        for institution in institutions:
            faculty_for_institution = [f for f in faculty_users if f.profile.institution == institution]
            if faculty_for_institution:  # Only create courses if we have faculty
                courses = self.create_courses(institution, faculty_for_institution, options['courses'])
                all_courses.extend(courses)
                
        # Create study groups
        self.create_study_groups(all_courses, all_users)
        
        # Create clubs and events
        self.create_community_content(institutions, all_users)
        
        # Create posts and interactions
        self.create_content(all_users, all_courses)
        
        # Create messages and group chats
        self.create_messages(all_users)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))
    
    def purge_data(self):
        """Remove all existing data"""
        self.stdout.write(self.style.WARNING('Purging existing data...'))
        MessageAttachment.objects.all().delete()
        Notification.objects.all().delete()
        GroupMessage.objects.all().delete()
        GroupChatMember.objects.all().delete()
        GroupChat.objects.all().delete()
        DirectMessage.objects.all().delete()
        Share.objects.all().delete()
        Like.objects.all().delete()
        UserInteraction.objects.all().delete()
        Comment.objects.all().delete()
        Post.objects.all().delete()
        ClubMember.objects.all().delete()
        Club.objects.all().delete()
        EventAttendee.objects.all().delete()
        Event.objects.all().delete()
        StudyGroupMember.objects.all().delete()
        StudyGroup.objects.all().delete()
        CourseEnrollment.objects.all().delete()
        Course.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()  # Keep superuser
        Campus.objects.all().delete()
        Institution.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Data purged successfully.'))

    def create_institutions(self, num_institutions, num_campuses_per_institution):
        """Create institutions and their campuses"""
        self.stdout.write(self.style.SUCCESS(f'Creating {num_institutions} institutions...'))
        institutions = []
        
        university_names = [
            'Riverside University', 'Highland College', 'Westview Institute of Technology',
            'Bayside State University', 'Lakeside College', 'Eastwood University',
            'Northern Technical Institute', 'Central Valley College', 'Sunset University',
            'Meadow Brook Institute'
        ]
        
        # Keep track of used names and domains to avoid duplicates
        used_names = set(Institution.objects.values_list('name', flat=True))
        used_domains = set(Institution.objects.values_list('domain', flat=True))
        
        created_count = 0
        attempts = 0
        max_attempts = num_institutions * 2  # Allow some extra attempts
        
        while created_count < num_institutions and attempts < max_attempts:
            attempts += 1
            
            # Select or generate a name
            if created_count < len(university_names):
                base_name = university_names[created_count]
            else:
                base_name = f"{fake.city()} University"
                
            # Generate unique name if needed
            name = base_name
            name_counter = 1
            while name in used_names:
                name = f"{base_name} {name_counter}"
                name_counter += 1
                
            # Generate unique domain
            base_domain = f"{name.lower().replace(' ', '')}.edu"
            domain = base_domain
            domain_counter = 1
            while domain in used_domains:
                domain = f"{base_domain.split('.')[0]}{domain_counter}.edu"
                domain_counter += 1
                
            # Add to tracking sets to prevent duplicates within this run
            used_names.add(name)
            used_domains.add(domain)
            
            try:
                institution = Institution.objects.create(
                    name=name,
                    domain=domain,
                    address=fake.address(),
                    timezone='Africa/Nairobi',
                    settings={
                        'academic_calendar': {'start_date': '2023-09-01', 'end_date': '2024-05-31'},
                        'features': {'events': True, 'clubs': True, 'courses': True}
                    }
                )
                institutions.append(institution)
                created_count += 1
                
                # Create campuses for each institution
                for j in range(num_campuses_per_institution):
                    campus_name = f"{fake.city()} Campus"
                    if j == 0:
                        campus_name = "Main Campus"
                        
                    Campus.objects.create(
                        institution=institution,
                        name=campus_name,
                        address=fake.address(),
                        latitude=float(fake.latitude()),
                        longitude=float(fake.longitude())
                    )
                
                self.stdout.write(f'  Created {institution.name} with {num_campuses_per_institution} campuses')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed to create institution {name}: {str(e)}"))
                
        if created_count == 0:
            self.stdout.write(self.style.ERROR('Failed to create any institutions. Try purging the database first.'))
        elif created_count < num_institutions:
            self.stdout.write(self.style.WARNING(f'Only created {created_count} out of {num_institutions} requested institutions.'))
    
        return institutions

    def create_users(self, institution, num_users):
        """Create users for an institution"""
        self.stdout.write(self.style.SUCCESS(f'Creating {num_users} users for {institution.name}...'))
        users = []
        faculty_users = []
        
        # Get all campuses for this institution
        campuses = list(Campus.objects.filter(institution=institution))
        
        roles = ['student', 'faculty', 'staff']
        role_weights = [0.8, 0.15, 0.05]  # 80% students, 15% faculty, 5% staff
        
        # Keep track of used student IDs to avoid duplicates
        used_student_ids = set()
        
        for i in range(num_users):
            role = random.choices(roles, weights=role_weights)[0]
            
            # Create base user
            username = f"{fake.user_name()}_{institution.name.lower().replace(' ', '')}"
            email = f"{username}@{institution.domain}"
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            user = User.objects.create_user(
                username=username[:30],  # Limit username length
                email=email,
                password="password123",  # Simple password for testing
                first_name=first_name,
                last_name=last_name,
                is_verified=True
            )
            
            # Create user profile with unique student_id
            campus = random.choice(campuses) if campuses else None
            
            # Generate a unique student ID for students
            student_id = ''
            if role == 'student':
                while True:
                    # Generate a unique ID with institution prefix
                    new_id = f"{institution.name[:3].upper()}{fake.random_number(digits=8)}"
                    if new_id not in used_student_ids:
                        used_student_ids.add(new_id)
                        student_id = new_id
                        break
            elif role == 'faculty':
                # Faculty IDs with different format to avoid uniqueness issues
                student_id = f"FAC-{institution.name[:3].upper()}{fake.random_number(digits=6)}"
            elif role == 'staff':
                # Staff IDs with different format
                student_id = f"STF-{institution.name[:3].upper()}{fake.random_number(digits=6)}"
                
            try:
                profile = UserProfile.objects.create(
                    user=user,
                    institution=institution,
                    campus=campus,
                    student_id=student_id,
                    role=role,
                    department=fake.job() if role in ['faculty', 'staff'] else fake.random_element(['Computer Science', 'Engineering', 'Business', 'Arts', 'Medicine']),
                    phone_number=fake.phone_number(),
                    dorm_building=fake.random_element(['North Hall', 'South Hall', 'East Hall', 'West Hall']) if role == 'student' else '',
                    room_number=f"{random.randint(1, 5)}0{random.randint(1, 9)}" if role == 'student' else '',
                    privacy_level=random.choice(['public', 'friends', 'private']),
                    preferred_content_types=['academic', 'social', 'events'],
                    interests={'tags': fake.words(nb=5)}
                )
                
                users.append(user)
                if role == 'faculty':
                    faculty_users.append(user)
            except Exception as e:
                # If profile creation fails, delete the user and continue
                self.stdout.write(self.style.WARNING(f"Failed to create profile for {username}: {str(e)}"))
                user.delete()
                
            if i % 10 == 0:
                self.stdout.write(f'  Created {i} users...')
                
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(users)} users for {institution.name}'))
        return users, faculty_users

    def create_courses(self, institution, faculty_users, num_courses):
        """Create courses for an institution"""
        self.stdout.write(self.style.SUCCESS(f'Creating {num_courses} courses for {institution.name}...'))
        courses = []
        
        # Course subjects and codes
        subjects = [
            ('CS', 'Computer Science'),
            ('MATH', 'Mathematics'),
            ('ENG', 'English'),
            ('PHYS', 'Physics'),
            ('CHEM', 'Chemistry'),
            ('BIO', 'Biology'),
            ('HIST', 'History'),
            ('ECON', 'Economics'),
            ('PSYC', 'Psychology'),
            ('ART', 'Art')
        ]
        
        current_year = timezone.now().year
        semesters = ['fall', 'spring', 'summer']
        
        for i in range(num_courses):
            subject, subject_name = random.choice(subjects)
            course_number = f"{random.randint(1, 4)}{random.randint(0, 9)}{random.randint(0, 9)}"
            course_code = f"{subject} {course_number}"
            
            course_name = f"Introduction to {subject_name}" if course_number.startswith('1') else \
                         f"Advanced {subject_name}" if course_number.startswith('4') else \
                         f"{fake.word().capitalize()} {subject_name}"
            
            instructor = random.choice(faculty_users)
            semester = random.choice(semesters)
            year = current_year
            
            course = Course.objects.create(
                institution=institution,
                course_code=course_code,
                course_name=course_name,
                semester=semester,
                year=year,
                instructor=instructor,
                description=fake.paragraph(),
                max_enrollment=random.randint(20, 200),
                enrollment_open=True
            )
            courses.append(course)
            
            # Create enrollment for instructor
            CourseEnrollment.objects.create(
                user=instructor,
                course=course,
                role='instructor'
            )
            
            # Select random students to enroll
            student_users = User.objects.filter(
                profile__institution=institution,
                profile__role='student'
            )[:30]
            
            # Enroll students
            for student in student_users:
                if random.random() < 0.3:  # 30% chance to enroll in each course
                    CourseEnrollment.objects.create(
                        user=student,
                        course=course,
                        role='student'
                    )
                    
        return courses

    def create_study_groups(self, courses, users):
        """Create study groups for courses"""
        self.stdout.write(self.style.SUCCESS('Creating study groups...'))
        
        for course in random.sample(courses, min(len(courses), 20)):
            # Get enrolled students
            enrolled_users = User.objects.filter(
                course_enrollments__course=course,
                course_enrollments__is_active=True
            )
            
            if enrolled_users.count() < 3:
                continue
                
            # Create 1-2 study groups per course
            num_groups = random.randint(1, 2)
            for i in range(num_groups):
                creator = random.choice(list(enrolled_users))
                
                group_name = f"{course.course_code} Study Group {i+1}"
                
                study_group = StudyGroup.objects.create(
                    name=group_name,
                    description=f"Study group for {course.course_name}. {fake.paragraph()}",
                    course=course,
                    creator=creator,
                    max_members=random.randint(5, 20),
                    is_private=random.choice([True, False]),
                    meeting_location=fake.random_element(['Library Room 101', 'Student Union', 'Coffee Shop', 'Online']),
                    meeting_time=timezone.now() + datetime.timedelta(days=random.randint(1, 14)),
                    meeting_frequency=random.choice(['weekly', 'biweekly', 'monthly', 'irregular'])
                )
                
                # Add members (creator is already added by the model's save method)
                for user in random.sample(list(enrolled_users), min(random.randint(3, 10), enrolled_users.count())):
                    if user != creator and random.random() < 0.7:  # 70% chance to join
                        try:
                            StudyGroupMember.objects.create(
                                group=study_group,
                                user=user,
                                role='member'
                            )
                        except:
                            # Skip if user can't join
                            pass
                            
        self.stdout.write(f'  Created study groups for {len(courses)} courses')

    def create_community_content(self, institutions, users):
        """Create clubs and events"""
        self.stdout.write(self.style.SUCCESS('Creating community content...'))
        
        # Create clubs for each institution
        for institution in institutions:
            num_clubs = random.randint(3, 10)
            institution_users = [u for u in users if hasattr(u, 'profile') and u.profile.institution == institution]
            
            if not institution_users:
                continue
                
            for i in range(num_clubs):
                president = random.choice(institution_users)
                
                club_categories = ['academic', 'social', 'sports', 'cultural', 'professional', 'service', 'hobby', 'religious']
                category = random.choice(club_categories)
                
                club_name = f"{fake.company()} {category.capitalize()} Club"
                
                club = Club.objects.create(
                    name=club_name,
                    description=fake.paragraph(),
                    institution=institution,
                    campus=random.choice(list(Campus.objects.filter(institution=institution))) if random.random() < 0.7 else None,
                    category=category,
                    president=president,
                    meeting_schedule=fake.random_element([
                        'Every Monday at 5 PM', 
                        'Tuesdays and Thursdays at 6 PM',
                        'Wednesdays at 7 PM',
                        'Fridays at 4 PM',
                        'Every other Saturday at 10 AM'
                    ]),
                    contact_email=f"{club_name.lower().replace(' ', '.')}@{institution.domain}",
                    max_members=random.randint(20, 100),
                    is_public=random.choice([True, False])
                )
                
                # Add members (president is already a member)
                ClubMember.objects.create(
                    club=club,
                    user=president,
                    role='president'
                )
                
                # Add some officers
                officer_count = random.randint(1, 3)
                for _ in range(officer_count):
                    officer = random.choice(institution_users)
                    if officer != president and not club.members.filter(user=officer).exists():
                        ClubMember.objects.create(
                            club=club,
                            user=officer,
                            role='officer'
                        )
                
                # Add regular members
                for user in random.sample(institution_users, min(random.randint(5, 30), len(institution_users))):
                    if not club.members.filter(user=user).exists():
                        ClubMember.objects.create(
                            club=club,
                            user=user,
                            role='member'
                        )
            
            # Create events for each institution
            num_events = random.randint(5, 15)
            for i in range(num_events):
                organizer = random.choice(institution_users)
                
                event_types = ['academic', 'social', 'sports', 'career', 'cultural', 'service']
                event_type = random.choice(event_types)
                
                start_date = timezone.now() + datetime.timedelta(days=random.randint(1, 30))
                
                event = Event.objects.create(
                    title=f"{fake.random_element(['Annual', 'Summer', 'Spring', 'Fall', 'Winter'])} {event_type.capitalize()} {fake.random_element(['Festival', 'Fair', 'Workshop', 'Seminar', 'Conference'])}",
                    description=fake.paragraph(),
                    organizer=organizer,
                    start_datetime=start_date,
                    end_datetime=start_date + datetime.timedelta(hours=random.randint(1, 8)),
                    location=fake.random_element(['Main Auditorium', 'Student Union', 'Sports Field', 'Library Hall', 'Lecture Room 101']),
                    event_type=event_type,
                    is_public=random.choice([True, False]),
                    max_attendees=random.randint(20, 200) if random.random() < 0.5 else None,
                    registration_required=random.choice([True, False]),
                    institution=institution,
                    campus=random.choice(list(Campus.objects.filter(institution=institution))) if random.random() < 0.7 else None,
                    tags=fake.words(nb=random.randint(2, 5))
                )
                
                # Add attendees
                for user in random.sample(institution_users, min(random.randint(5, 50), len(institution_users))):
                    try:
                        EventAttendee.objects.create(
                            event=event,
                            user=user,
                            status=random.choices(['going', 'interested'], weights=[0.7, 0.3])[0]
                        )
                    except:
                        pass
                        
        self.stdout.write(f'  Created clubs and events for {len(institutions)} institutions')

    def create_content(self, users, courses):
        """Create posts, comments, likes, and shares"""
        self.stdout.write(self.style.SUCCESS('Creating content posts and interactions...'))
        
        post_types = ['text', 'image', 'video', 'event', 'marketplace']
        visibility_options = ['public', 'friends', 'course', 'anonymous']
        
        # Create some posts
        posts = []
        num_posts = min(len(users) * 2, 200)  # Up to 2 posts per user, max 200
        
        for _ in range(num_posts):
            author = random.choice(users)
            post_type = random.choice(post_types)
            visibility = random.choice(visibility_options)
            
            post = Post.objects.create(
                author=author,
                content=fake.paragraph(),
                post_type=post_type,
                visibility=visibility,
                course=random.choice(courses) if visibility == 'course' and courses else None,
                location=author.profile.campus if hasattr(author, 'profile') and author.profile.campus else None,
                is_pinned=random.random() < 0.05,  # 5% chance to be pinned
                is_anonymous=visibility == 'anonymous',
                tags=fake.words(nb=random.randint(1, 5))
            )
            posts.append(post)
            
            # Create user interaction for the author viewing their own post
            try:
                UserInteraction.objects.create(
                    user=author,
                    post=post,
                    interaction_type='view',
                    dwell_time=random.uniform(10, 60)
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not create interaction: {str(e)}"))
    
        # Create comments on posts
        for post in posts:
            num_comments = random.randint(0, 5)
            
            for _ in range(num_comments):
                commenter = random.choice(users)
                
                comment = Comment.objects.create(
                    post=post,
                    author=commenter,
                    content=fake.sentence(),
                    is_anonymous=random.random() < 0.1  # 10% chance to be anonymous
                )
                
                # Create interaction for commenting
                try:
                    # Check if comment interaction already exists
                    if not UserInteraction.objects.filter(
                        user=commenter, 
                        post=post, 
                        interaction_type='comment'
                    ).exists():
                        UserInteraction.objects.create(
                            user=commenter,
                            post=post,
                            interaction_type='comment',
                            dwell_time=random.uniform(20, 120)
                        )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not create comment interaction: {str(e)}"))
            
        # Create likes
        for post in posts:
            num_likes = random.randint(0, 10)
            likers = random.sample(users, min(num_likes, len(users)))
            
            for liker in likers:
                Like.objects.create(
                    user=liker,
                    post=post
                )
                
                # Create interaction for liking
                try:
                    # Check if like interaction already exists
                    if not UserInteraction.objects.filter(
                        user=liker, 
                        post=post, 
                        interaction_type='like'
                    ).exists():
                        UserInteraction.objects.create(
                            user=liker,
                            post=post,
                            interaction_type='like',
                            dwell_time=random.uniform(5, 30)
                        )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not create like interaction: {str(e)}"))
            
        # Create shares
        for post in posts:
            if random.random() < 0.2:  # 20% chance for a post to be shared
                num_shares = random.randint(1, 3)
                sharers = random.sample(users, min(num_shares, len(users)))
                
                for sharer in sharers:
                    Share.objects.create(
                        user=sharer,
                        post=post,
                        caption=fake.sentence() if random.random() < 0.5 else ''
                    )
                    
                    # Create interaction for sharing
                    try:
                        # Check if share interaction already exists
                        if not UserInteraction.objects.filter(
                            user=sharer, 
                            post=post, 
                            interaction_type='share'
                        ).exists():
                            UserInteraction.objects.create(
                                user=sharer,
                                post=post,
                                interaction_type='share',
                                dwell_time=random.uniform(15, 60)
                            )
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Could not create share interaction: {str(e)}"))
                
        # Create additional view interactions
        for _ in range(min(len(users) * 5, 500)):  # Up to 5 views per user, max 500
            viewer = random.choice(users)
            post = random.choice(posts)
            
            # Skip if user already has a view interaction with this post
            if UserInteraction.objects.filter(user=viewer, post=post, interaction_type='view').exists():
                continue
            
            try:    
                UserInteraction.objects.create(
                    user=viewer,
                    post=post,
                    interaction_type='view',
                    dwell_time=random.uniform(3, 180)
                )
            except Exception as e:
                # Skip silently on duplicate interaction
                pass
            
        self.stdout.write(f'  Created {len(posts)} posts with comments, likes, and shares')

    def create_messages(self, users):
        """Create messages between users and in group chats"""
        self.stdout.write(self.style.SUCCESS('Creating messages and group chats...'))
        
        # Create direct messages between random users
        num_conversations = min(len(users) * 2, 200)  # Up to 2 conversations per user, max 200
        
        for _ in range(num_conversations):
            sender = random.choice(users)
            recipient = random.choice([u for u in users if u != sender])
            
            # Create 1-5 messages in each direction
            for i in range(random.randint(1, 5)):
                DirectMessage.objects.create(
                    sender=sender,
                    recipient=recipient,
                    content=fake.paragraph(),
                    is_read=random.random() < 0.7  # 70% chance to be read
                )
                
            for i in range(random.randint(0, 3)):  # Recipient might not always reply
                DirectMessage.objects.create(
                    sender=recipient,
                    recipient=sender,
                    content=fake.paragraph(),
                    is_read=random.random() < 0.5  # 50% chance to be read
                )
        
        # Create group chats
        num_group_chats = min(len(users) // 5, 20)  # 1 chat per 5 users, max 20
        
        for i in range(num_group_chats):
            creator = random.choice(users)
            
            group_chat = GroupChat.objects.create(
                name=fake.random_element([
                    "Study Group", "Project Team", "Friends Chat", 
                    "Gaming Squad", "Course Discussion", "Event Planning"
                ]) + f" {i+1}",
                description=fake.sentence(),
                creator=creator,
                is_private=random.choice([True, False]),
                max_members=random.randint(10, 50)
            )
            
            # Add members (creator is automatically added as admin in the model's save method)
            num_members = random.randint(3, 10)
            members = random.sample([u for u in users if u != creator], min(num_members, len(users)-1))
            
            members_to_add = []
            for member in members:
                try:
                    chat_member = GroupChatMember.objects.create(
                        chat=group_chat,
                        user=member,
                        is_admin=random.random() < 0.2  # 20% chance to be admin
                    )
                    members_to_add.append(member)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not add {member} to group: {str(e)}"))
        
            # Add messages - ensure we're using confirmed members
            all_members = [creator] + members_to_add  # Only use members we successfully added
            num_messages = random.randint(5, 20)
            
            for _ in range(num_messages):
                sender = random.choice(all_members)
                
                # Double-check that sender is actually a member before creating message
                if group_chat.is_member(sender):
                    try:
                        GroupMessage.objects.create(
                            chat=group_chat,
                            sender=sender,
                            content=fake.paragraph()
                        )
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(
                            f"Failed to create group message from {sender} in {group_chat.name}: {str(e)}"
                        ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Skipping message creation: {sender} is not a member of {group_chat.name}"
                    ))
    
        # Create notifications
        num_notifications = min(len(users) * 3, 300)  # Up to 3 notifications per user, max 300
        
        notification_types = ['like', 'comment', 'share', 'message', 'group_message', 
                             'event', 'follow', 'mention', 'group_invite', 'system']
                             
        for _ in range(num_notifications):
            user = random.choice(users)
            notification_type = random.choice(notification_types)
            actor = random.choice([u for u in users if u != user]) if notification_type != 'system' else None
            
            Notification.objects.create(
                user=user,
                type=notification_type,
                title=f"New {notification_type.replace('_', ' ').title()}",
                content=fake.sentence(),
                actor=actor,
                is_read=random.random() < 0.5  # 50% chance to be read
            )
                
        self.stdout.write(f'  Created direct messages, group chats, and notifications')
