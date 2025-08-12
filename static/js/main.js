document.addEventListener('DOMContentLoaded', () => {
    const likeButtons = document.querySelectorAll('.like-btn');
    const commentForms = document.querySelectorAll('.comment-form');
    const replyButtons = document.querySelectorAll('.reply-btn');
    const followButtons = document.querySelectorAll('.follow-btn');
    const shareButtons = document.querySelectorAll('.share-btn');
    const videoFeed = document.querySelector('.video-feed');
    const profilePic = document.querySelector('#profile-pic');
    const profilePicPopup = document.querySelector('#profile-pic-popup');
    let currentVideoIndex = 0;

    likeButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const videoId = button.dataset.videoId;
            const liked = button.dataset.liked === 'true';
            const response = await fetch(`/like/${videoId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.status === 'liked') {
                button.dataset.liked = 'true';
                button.querySelector('.heart-icon').textContent = '♥';
                button.querySelector('.like-count').textContent = data.likes;
            } else if (data.status === 'unliked') {
                button.dataset.liked = 'false';
                button.querySelector('.heart-icon').textContent = '♡';
                button.querySelector('.like-count').textContent = data.likes;
            }
        });
    });

    commentForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const videoId = form.dataset.videoId;
            const formData = new FormData(form);
            const parentId = formData.get('parent_id') || null;
            const response = await fetch(`/comment/${videoId}`, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (data.status === 'success') {
                const commentSection = form.closest('.comment-section');
                const commentDiv = document.createElement('div');
                commentDiv.dataset.commentId = data.comment.id;
                if (parentId) {
                    commentDiv.classList.add('reply');
                    const parentComment = commentSection.querySelector(`[data-comment-id="${parentId}"]`);
                    commentDiv.innerHTML = `
                        <p><strong>${data.comment.user.firstname} ${data.comment.user.lastname}</strong>: ${data.comment.content}</p>
                    `;
                    parentComment.appendChild(commentDiv);
                } else {
                    commentDiv.classList.add('comment');
                    commentDiv.innerHTML = `
                        <p><strong>${data.comment.user.firstname} ${data.comment.user.lastname}</strong>: ${data.comment.content}</p>
                        <button class="action-btn reply-btn" data-comment-id="${data.comment.id}">Reply</button>
                    `;
                    commentSection.insertBefore(commentDiv, form);
                }
                form.querySelector('input[name="content"]').value = '';
                form.querySelector('input[name="parent_id"]').value = '';
                attachReplyButtonListeners();
            }
        });
    });

    function attachReplyButtonListeners() {
        const replyButtons = document.querySelectorAll('.reply-btn');
        replyButtons.forEach(button => {
            button.removeEventListener('click', replyHandler);
            button.addEventListener('click', replyHandler);
        });
    }

    function replyHandler() {
        const commentId = this.dataset.commentId;
        const form = this.closest('.video-card').querySelector('.comment-form');
        form.querySelector('input[name="parent_id"]').value = commentId;
        form.querySelector('input[name="content"]').focus();
    }

    attachReplyButtonListeners();

    followButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const userId = button.dataset.userId;
            const followed = button.dataset.followed === 'true';
            const response = await fetch(`/follow/${userId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.status === 'followed') {
                button.textContent = 'Unfollow';
                button.dataset.followed = 'true';
            } else if (data.status === 'unfollowed') {
                button.textContent = 'Follow';
                button.dataset.followed = 'false';
            }
        });
    });

    shareButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const videoId = button.dataset.videoId;
            const response = await fetch(`/share/${videoId}`);
            const data = await response.json();
            if (data.status === 'success') {
                const popup = document.createElement('div');
                popup.classList.add('share-popup');
                popup.innerHTML = `
                    <input type="text" value="${data.share_url}" readonly>
                    <button onclick="this.previousElementSibling.select(); document.execCommand('copy'); this.textContent='Copied!'">Copy Link</button>
                `;
                document.body.appendChild(popup);
                setTimeout(() => {
                    popup.style.display = 'flex';
                }, 10);
                setTimeout(() => {
                    popup.style.opacity = '0';
                    setTimeout(() => popup.remove(), 300);
                }, 5000);
            }
        });
    });

    if (profilePic && profilePicPopup) {
        profilePic.addEventListener('click', () => {
            profilePicPopup.style.display = 'flex';
        });
    }

    if (videoFeed) {
        const videos = document.querySelectorAll('.video-card');
        const observerOptions = {
            root: null,
            threshold: 0.8
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const video = entry.target.querySelector('video');
                if (entry.isIntersecting) {
                    video.play();
                    currentVideoIndex = Array.from(videos).indexOf(entry.target);
                } else {
                    video.pause();
                }
            });
        }, observerOptions);

        videos.forEach(video => observer.observe(video));

        videoFeed.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY;
            if (delta > 0 && currentVideoIndex < videos.length - 1) {
                currentVideoIndex++;
            } else if (delta < 0 && currentVideoIndex > 0) {
                currentVideoIndex--;
            }
            videos[currentVideoIndex].scrollIntoView({ behavior: 'smooth' });
        });

        let touchStartY = 0;
        videoFeed.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
        });

        videoFeed.addEventListener('touchend', (e) => {
            const touchEndY = e.changedTouches[0].clientY;
            const delta = touchStartY - touchEndY;
            if (delta > 50 && currentVideoIndex < videos.length - 1) {
                currentVideoIndex++;
            } else if (delta < -50 && currentVideoIndex > 0) {
                currentVideoIndex--;
            }
            videos[currentVideoIndex].scrollIntoView({ behavior: 'smooth' });
        });
    }
});