(async function(){
  // JSZip 불러오기
  if (typeof JSZip === 'undefined') {
    await new Promise(resolve => {
      var script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.0/jszip.min.js';
      script.onload = resolve;
      document.head.appendChild(script);
    });
    console.log('JSZip 로드 완료');
  }

  // 전체 리뷰 개수 파싱
  var reviewCountText = document.querySelector('#reviewCount')?.textContent || '';
  console.log('리뷰 카운트 텍스트:', reviewCountText);
  
  // 여러 패턴으로 숫자 추출 시도 
  // (1,000 : 천 단위 리뷰 파싱 가능)
  var totalReviewCount = 0;
  var patterns = [
    /\((\d{1,3}(?:,\d{3})*)\)/,  // 콤마 포함 숫자: (1,234)
    /\((\d+)\)/,                  // 기본 숫자: (1234)
    /(\d{1,3}(?:,\d{3})*)/,      // 콤마 포함 숫자 (괄호 없음)
    /(\d+)/                       // 아무 숫자나
  ];
  
  for (var pattern of patterns) {
    var match = reviewCountText.match(pattern);
    if (match) {
      // 콤마 제거하고 숫자로 변환
      totalReviewCount = parseInt(match[1].replace(/,/g, ''));
      console.log('패턴 매치:', pattern, '결과:', totalReviewCount);
      break;
    }
  }
  
  console.log('전체 리뷰 개수:', totalReviewCount);
  
  if (totalReviewCount === 0) {
    console.log('리뷰 개수를 파싱할 수 없습니다. 수동으로 확인해주세요.');
    // 현재 로드된 리뷰로 계속 진행
    var currentItems = document.querySelectorAll('#divReviewList li[data-review-id]');
    if (currentItems.length === 0) {
      console.log('리뷰가 없습니다.');
      return;
    }
    console.log('현재 로드된 리뷰로 진행:', currentItems.length);
  }

  // 현재 로드된 리뷰 개수 확인
  var getCurrentReviewCount = function() {
    return document.querySelectorAll('#divReviewList li[data-review-id]').length;
  };

  // 모든 리뷰 로드하기
  console.log('모든 리뷰 로드 시작...');
  var currentCount = getCurrentReviewCount();
  console.log('현재 로드된 리뷰:', currentCount);

  var retryCount = 0;
  var maxRetries = 5;
  var consecutiveFailures = 0;  // 연속 실패 횟수 추가
  
  // totalReviewCount가 0이면 무한 루프 방지를 위해 최대 시도 횟수 설정
  var maxAttempts = totalReviewCount > 0 ? totalReviewCount : 100;
  var attemptCount = 0;
  
  while (currentCount < totalReviewCount || (totalReviewCount === 0 && attemptCount < maxAttempts)) {
    attemptCount++;
    
    if (totalReviewCount > 0) {
      console.log(`진행률: ${currentCount}/${totalReviewCount} (${Math.round(currentCount/totalReviewCount*100)}%)`);
    } else {
      console.log(`현재 로드된 리뷰: ${currentCount}개 (시도 ${attemptCount}/${maxAttempts})`);
    }
    
    // 더보기 버튼 찾기 및 클릭
    var moreBtn = document.querySelector('#reviewMoreBtn');
    if (!moreBtn) {
      console.log('더보기 버튼을 찾을 수 없습니다.');
      break;
    }
    
    // 버튼이 숨겨져 있는지 확인
    if (moreBtn.style.display === 'none' || moreBtn.offsetParent === null) {
      console.log('더보기 버튼이 숨겨져 있습니다. 로드 완료');
      break;
    }
    
    // 버튼 클릭
    console.log('더보기 버튼 클릭...');
    moreBtn.click();

    // 로딩 대기 (2초)
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    var newCount = getCurrentReviewCount();
    console.log('클릭 후 리뷰 개수:', newCount);
    
    if (newCount === currentCount) {
      retryCount++;
      consecutiveFailures++;
      console.log(`리뷰가 추가되지 않았습니다. 재시도 ${retryCount}/${maxRetries} (연속 실패: ${consecutiveFailures})`);
      
      // 연속 실패가 3번 이상이면 종료
      if (consecutiveFailures >= 3) {
        console.log('연속 실패 횟수가 너무 많습니다. 로드 완료로 간주합니다.');
        break;
      }
      
      if (retryCount >= maxRetries) {
        console.log('최대 재시도 횟수에 도달했습니다.');
        
        // 페이지 새로고침 후 더보기 버튼 다시 찾기
        console.log('페이지를 스크롤하여 더보기 버튼을 다시 찾습니다...');
        moreBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 한 번 더 시도
        var retryBtn = document.querySelector('#reviewMoreBtn');
        if (retryBtn && retryBtn.style.display !== 'none' && retryBtn.offsetParent !== null) {
          console.log('재시도 버튼 클릭...');
          retryBtn.click();
          await new Promise(resolve => setTimeout(resolve, 3000));
          
          var finalCount = getCurrentReviewCount();
          if (finalCount === currentCount) {
            console.log('더 이상 리뷰를 로드할 수 없습니다.');
            break;
          } else {
            currentCount = finalCount;
            retryCount = 0;
            consecutiveFailures = 0;  // 성공하면 연속 실패 리셋
            continue;
          }
        } else {
          console.log('더보기 버튼이 완전히 사라졌습니다.');
          break;
        }
      }
      
      // 재시도 대기 시간 증가
      await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
    } else {
      currentCount = newCount;
      retryCount = 0;  // 성공하면 재시도 카운트 리셋
      consecutiveFailures = 0;  // 성공하면 연속 실패 리셋
    }
  }

  console.log('모든 리뷰 로드 완료! 총', currentCount, '개');

  // ZIP 파일 생성
  var zip = new JSZip();
  var reviewItems = document.querySelectorAll('#divReviewList li[data-review-id]');
  
  console.log('ZIP 파일 생성 시작...');
  
  reviewItems.forEach(function(reviewItem, index){
    var modelId = reviewItem.getAttribute('data-model-id') || 'unknownModel';
    var reviewId = reviewItem.getAttribute('data-review-id') || 'unknownId';
    var fileName = modelId + '_' + reviewId + '.txt';
    
    // 별점 정보
    var starText = reviewItem.querySelector('.star-wrap .blind')?.textContent || '';
    var starMatch = starText.match(/([0-9.]+)점/);
    var star = starMatch ? starMatch[1] : '';
    
    // 평가 요약
    var starTextSummary = reviewItem.querySelector('.score-wrap .txt')?.textContent.trim() || '';
    
    // 세부 평가 항목들
    var ratings = Array.from(reviewItem.querySelectorAll('.rating-list li')).map(function(li){
      var key = li.querySelector('dt')?.textContent.trim() || '';
      var val = li.querySelector('dd')?.textContent.trim() || '';
      return key + ': ' + val;
    });
    
    // 사용자 정보
    var userName = reviewItem.querySelector('.user-name')?.textContent.replace(/^\s*구매자 이름\s*/, '').trim() || '';
    var purchaseDate = reviewItem.querySelector('.purchase-date')?.textContent.replace(/^\s*구매 일자\s*/, '').trim() || '';
    
    // 리뷰 본문
    var message = reviewItem.querySelector('.message')?.innerText.trim() || '';
    
    // 이미지 URL들
    var imgUrls = Array.from(reviewItem.querySelectorAll('.media-list .thumb img')).map(function(img){
      var url = img.getAttribute('src');
      if(url && url.startsWith('/kr')) {
        url = 'https://www.lge.co.kr' + url;
      }
      return url;
    }).filter(url => url);
    
    // 동영상 URL들
    var videoUrls = Array.from(reviewItem.querySelectorAll('.media-list video')).map(function(video){
      var url = video.getAttribute('src');
      if(url && url.startsWith('/kr')) {
        url = 'https://www.lge.co.kr' + url;
      }
      return url;
    }).filter(url => url);
    
    // 파일 내용 구성
    var result = [
      '별점: ' + star,
      '평가: ' + starTextSummary,
      '주요항목 평가:',
      ratings.map(function(r){ return '- ' + r; }).join('\n'),
      '작성자: ' + userName,
      '구매일자: ' + purchaseDate,
      '리뷰 본문:',
      message,
      '이미지 URL:',
      imgUrls.map(function(url){ return '- ' + url; }).join('\n'),
      '동영상 URL:',
      videoUrls.map(function(url){ return '- ' + url; }).join('\n')
    ].join('\n\n');
    
    zip.file(fileName, result);
    
    if ((index + 1) % 50 === 0) {
      console.log('진행률:', index + 1, '/', reviewItems.length);
    }
  });
  
  console.log('ZIP 파일 생성 중...');
  var blob = await zip.generateAsync({type:"blob"});
  
  // 다운로드
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = 'reviews_all_' + reviewItems.length + '.zip';
  a.click();
  URL.revokeObjectURL(url);
  
  console.log('ZIP 다운로드 완료! 총', reviewItems.length, '개 리뷰');
})();