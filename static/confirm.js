function confirm(){
    const reg_no = document.querySelector('#regNo').value;
    alert(`${reg_no} grade updated!`);
}

document.addEventListener('DOMContentLoaded', function(){
    document.querySelector('button').addEventListener('click', confirm);
});