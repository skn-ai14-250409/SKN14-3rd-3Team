(function() {
  // 제품명 추출
  var productNameElement = document.querySelector('.product-name .name');
  var productName = '';
  if (productNameElement) {
    // 기본 제품명 (sub-text-new 제외)
    var nameText = productNameElement.childNodes[0]?.textContent?.trim() || '';
    
    // sub-text-new 내의 항목들
    var subTextItems = Array.from(productNameElement.querySelectorAll('.sub-text-new .item')).map(function(item) {
      return item.textContent.trim();
    });
    
    // 결합: 제품명 + | + 각 항목들
    var parts = [nameText.replace(/\s+/g, '')];
    subTextItems.forEach(function(item) {
      parts.push(item);
    });
    
    productName = parts.join(' |');
  }
  
  // 모델명 추출 (blind 텍스트 제거)
  var modelNameElement = document.querySelector('.sku.copy');
  var modelName = '';
  if (modelNameElement) {
    var blindElement = modelNameElement.querySelector('.blind');
    if (blindElement) {
      blindElement.remove();
    }
    modelName = modelNameElement.textContent.trim();
  }
  
  // 리뷰 개수 추출
  var reviewCountText = document.querySelector('#reviewCount')?.textContent || '';
  console.log('리뷰 카운트 텍스트:', reviewCountText);
  
  var reviewCount = '0';
  var patterns = [
    /\((\d{1,3}(?:,\d{3})*)\)/,  // 콤마 포함 숫자: (1,234)
    /\((\d+)\)/,                  // 기본 숫자: (1234)
    /(\d{1,3}(?:,\d{3})*)/,      // 콤마 포함 숫자 (괄호 없음)
    /(\d+)/                       // 아무 숫자나
  ];
  
  for (var pattern of patterns) {
    var match = reviewCountText.match(pattern);
    if (match) {
      // 콤마 제거하고 숫자로 변환 후 다시 문자열로 (천 단위 수집 가능)
      reviewCount = match[1].replace(/,/g, '');
      console.log('패턴 매치:', pattern, '결과:', reviewCount);
      break;
    }
  }

  // 별점
  var reviewScore = document.querySelector('#reviewScore')?.textContent.trim() || '0';

  // 장점 키워드
  var keywords = Array.from(document.querySelectorAll('.summary-wrap li')).map(function(li) {
    var text = li.querySelector('.summary')?.textContent.trim() || '';
    var percent = li.querySelector('.percent')?.textContent.trim() || '';
    return '- ' + text + ' ' + percent;
  });

  // 최종 문자열 조립
  var result = [
    '제품명 : ' + productName,
    '모델명 : ' + modelName,
    '리뷰개수 : ' + reviewCount,
    '별점 : ' + reviewScore,
    '장점 키워드',
    ...keywords
  ].join('\n');

  console.log(result);

  // 파일로 저장 (모델명을 파일명으로 사용)
  var fileName = modelName || 'review_summary';
  // 파일명에서 특수문자 제거
  fileName = fileName.replace(/[<>:"/\\|?*]/g, '_');
  
  var blob = new Blob([result], {type: 'text/plain'});
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = fileName + '.txt';
  a.click();
  URL.revokeObjectURL(url);
})();